#!/usr/bin/env python3
"""Score the frozen NONORM TUM confirmation panel with CONCH."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import torch
import torch.nn.functional as F
from datasets import load_dataset
from sklearn.metrics import accuracy_score

from build_tum_confirmation_panel import HF_BASE, LABEL_NAMES, NONORM_TUM_SHARDS
from score_conch_crc_val import load_crc_prompts


def stream_selected(panel: pd.DataFrame):
    wanted = {
        (row.stream_shard, int(row.stream_local_seen_index)): row
        for row in panel.itertuples(index=False)
    }
    for shard in NONORM_TUM_SHARDS:
        ds = load_dataset("parquet", data_files=HF_BASE + shard, split="train", streaming=True)
        for local_idx, ex in enumerate(ds):
            key = (shard, int(local_idx))
            row = wanted.get(key)
            if row is None:
                continue
            yield row, ex["image"].convert("RGB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conch-source", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--prompt-json", type=Path, required=True)
    ap.add_argument("--panel", type=Path, default=Path("spectra_ready_dataset/tum_confirmation_panel.csv"))
    ap.add_argument("--out", type=Path, default=Path("artifacts/tum_confirmation/target_model_results_tum_confirmation.csv"))
    ap.add_argument("--summary", type=Path, default=Path("artifacts/tum_confirmation/summary.json"))
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--force-exit", action="store_true")
    args = ap.parse_args()

    sys.path.insert(0, str(args.conch_source))
    from conch.downstream.zeroshot_path import zero_shot_classifier
    from conch.open_clip_custom import create_model_from_pretrained

    panel = pd.read_csv(args.panel)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"device={device}", flush=True)
    model, preprocess = create_model_from_pretrained(
        "conch_ViT-B-16", checkpoint_path=str(args.checkpoint), device=device
    )
    model.eval()
    classnames, templates = load_crc_prompts(args.prompt_json)
    with torch.inference_mode():
        classifier = zero_shot_classifier(model, classnames, templates, device=device)
    logit_scale = float(model.logit_scale.exp().detach().cpu().item())

    rows = []
    batch_tensors = []
    batch_meta = []

    def flush_batch():
        nonlocal batch_tensors, batch_meta, rows
        if not batch_tensors:
            return
        imgs = torch.stack(batch_tensors, dim=0).to(device, non_blocking=True)
        with torch.inference_mode():
            image_features = model.encode_image(imgs)
            logits = image_features @ classifier
            probs = F.softmax(logits * logit_scale, dim=1)
            preds = logits.argmax(dim=1)
        logits_np = logits.detach().cpu().numpy()
        probs_np = probs.detach().cpu().numpy()
        preds_np = preds.detach().cpu().numpy()
        for meta, logit_row, prob_row, pred in zip(batch_meta, logits_np, probs_np, preds_np):
            out = {
                "sample_id": meta.sample_id,
                "label": int(meta.label),
                "label_name": meta.label_name,
                "pred": int(pred),
                "pred_label_name": LABEL_NAMES[int(pred)],
                "correct": int(int(pred) == int(meta.label)),
            }
            for i in range(len(LABEL_NAMES)):
                out[f"logit_{LABEL_NAMES[i]}"] = float(logit_row[i])
                out[f"prob_{LABEL_NAMES[i]}"] = float(prob_row[i])
            rows.append(out)
        batch_tensors = []
        batch_meta = []

    for row, image in stream_selected(panel):
        batch_tensors.append(preprocess(image))
        batch_meta.append(row)
        if len(batch_tensors) >= args.batch_size:
            flush_batch()
            if len(rows) % (args.batch_size * 5) == 0:
                print(f"scored={len(rows)}", flush=True)
    flush_batch()
    df = pd.DataFrame(rows)
    if len(df) != len(panel):
        raise RuntimeError(f"Scored {len(df)} rows for panel of {len(panel)}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    summary = {
        "n": int(len(df)),
        "accuracy_tum_recall": float(accuracy_score(df["label"], df["pred"])),
        "prediction_counts": {LABEL_NAMES[int(k)]: int(v) for k, v in df["pred"].value_counts().sort_index().items()},
    }
    args.summary.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2), flush=True)
    if args.force_exit:
        os._exit(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
