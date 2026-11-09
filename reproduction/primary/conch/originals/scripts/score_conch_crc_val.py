#!/usr/bin/env python3
"""Score CRC-VAL with CONCH zero-shot prompts after axes are frozen."""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score


LABEL_NAMES = {
    0: "ADI",
    1: "BACK",
    2: "DEB",
    3: "LYM",
    4: "MUC",
    5: "MUS",
    6: "NORM",
    7: "STR",
    8: "TUM",
}


def iter_crc_val(parquet_dir: Path):
    idx = 0
    for parquet_path in sorted(parquet_dir.glob("CRC_VAL_HE_7K-*.parquet")):
        pf = pq.ParquetFile(parquet_path)
        for rg in range(pf.num_row_groups):
            table = pf.read_row_group(rg, columns=["image", "label"])
            labels = table["label"].to_pylist()
            images = table["image"].to_pylist()
            for label, img_struct in zip(labels, images):
                raw = img_struct["bytes"]
                path = img_struct.get("path") or ""
                yield {
                    "source_record_index": idx,
                    "sample_id": f"crcval_{idx:05d}",
                    "image_path": path,
                    "label": int(label),
                    "label_name": LABEL_NAMES[int(label)],
                    "image": Image.open(io.BytesIO(raw)).convert("RGB"),
                }
                idx += 1


def load_crc_prompts(path: Path):
    obj = json.loads(path.read_text())
    prompt_set = obj["0"]
    cn = prompt_set["classnames"]
    classnames = [cn[LABEL_NAMES[i]] for i in range(len(LABEL_NAMES))]
    return classnames, prompt_set["templates"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conch-source", type=Path, required=True)
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--prompt-json", type=Path, required=True)
    ap.add_argument("--parquet-dir", type=Path, default=Path("data_cache/parquets"))
    ap.add_argument("--frozen-table", type=Path, default=Path("spectra_ready_dataset/spectra_ready_table.csv"))
    ap.add_argument("--out", type=Path, default=Path("target_model_results.csv"))
    ap.add_argument("--summary", type=Path, default=Path("artifacts/target_model_summary.json"))
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    sys.path.insert(0, str(args.conch_source))
    from conch.downstream.zeroshot_path import zero_shot_classifier
    from conch.open_clip_custom import create_model_from_pretrained

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
    print(f"classifier_shape={tuple(classifier.shape)} logit_scale={logit_scale:.6f}", flush=True)

    frozen = pd.read_csv(args.frozen_table, usecols=["sample_id", "image_path", "label", "label_name"])
    expected = frozen.to_dict("records")
    rows = []
    batch_tensors = []
    batch_meta = []
    total = 0

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
                "sample_id": meta["sample_id"],
                "source_record_index": int(meta["source_record_index"]),
                "image_path": meta["image_path"],
                "label": int(meta["label"]),
                "label_name": meta["label_name"],
                "pred": int(pred),
                "pred_label_name": LABEL_NAMES[int(pred)],
                "correct": int(pred == int(meta["label"])),
            }
            for i in range(len(LABEL_NAMES)):
                out[f"logit_{LABEL_NAMES[i]}"] = float(logit_row[i])
                out[f"prob_{LABEL_NAMES[i]}"] = float(prob_row[i])
            rows.append(out)
        batch_tensors = []
        batch_meta = []

    for rec in iter_crc_val(args.parquet_dir):
        if args.limit and total >= args.limit:
            break
        exp = expected[total]
        if rec["sample_id"] != exp["sample_id"] or int(rec["label"]) != int(exp["label"]):
            raise RuntimeError(f"Frozen table mismatch at row {total}: {rec['sample_id']} vs {exp}")
        batch_tensors.append(preprocess(rec["image"]))
        batch_meta.append({k: v for k, v in rec.items() if k != "image"})
        total += 1
        if len(batch_tensors) >= args.batch_size:
            flush_batch()
            if total % (args.batch_size * 10) == 0:
                print(f"scored={total}", flush=True)
    flush_batch()

    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)
    y_true = df["label"].to_numpy()
    y_pred = df["pred"].to_numpy()
    report = classification_report(y_true, y_pred, labels=list(LABEL_NAMES), target_names=list(LABEL_NAMES.values()), output_dict=True, zero_division=0)
    summary = {
        "n": int(len(df)),
        "limit": int(args.limit),
        "device": str(device),
        "checkpoint": str(args.checkpoint),
        "prompt_json": str(args.prompt_json),
        "class_order": LABEL_NAMES,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "classification_report": report,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: summary[k] for k in ["n", "accuracy", "balanced_accuracy", "macro_f1", "weighted_f1"]}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
