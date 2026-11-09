#!/usr/bin/env python3
"""Freeze an outcome-informed TUM/tissue-fraction confirmation panel."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import load_dataset

from build_crc_candidate_table import LABEL_NAMES, image_features


HF_BASE = "https://huggingface.co/datasets/1aurent/NCT-CRC-HE/resolve/main/"
NONORM_TUM_SHARDS = [
    "data/NCT_CRC_HE_100K_NONORM-00017-of-00031-185be2828f60b3a7.parquet",
    "data/NCT_CRC_HE_100K_NONORM-00018-of-00031-20db16691204a5c6.parquet",
    "data/NCT_CRC_HE_100K_NONORM-00019-of-00031-9be5fae292c61245.parquet",
]
TISSUE_COLS = ["tissue_fraction", "white_fraction", "dark_fraction", "saturation_high_fraction"]


def assign_similarity_levels(values: pd.Series, n_levels: int) -> tuple[pd.Series, list[float]]:
    ranks = values.rank(method="first", ascending=False)
    return (pd.qcut(ranks, q=n_levels, labels=False) + 1).astype(int), [
        float(values.quantile(q)) for q in np.linspace(0, 1, n_levels + 1)
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nct-reference", type=Path, default=Path("spectra_ready_dataset/nct_reference_features.csv"))
    ap.add_argument("--out", type=Path, default=Path("spectra_ready_dataset/tum_confirmation_panel.csv"))
    ap.add_argument("--axis-ledger", type=Path, default=Path("axis_ledger.json"))
    ap.add_argument("--per-shard", type=int, default=600)
    ap.add_argument("--levels", type=int, default=6)
    ap.add_argument("--force-exit", action="store_true")
    args = ap.parse_args()

    ref = pd.read_csv(args.nct_reference)
    ref_tissue_median = ref[TISSUE_COLS].median()
    rows = []
    for shard_idx, shard in enumerate(NONORM_TUM_SHARDS):
        ds = load_dataset("parquet", data_files=HF_BASE + shard, split="train", streaming=True)
        taken = 0
        for local_idx, ex in enumerate(ds):
            if int(ex["label"]) != 8:
                continue
            feats = image_features(ex["image"])
            row = {
                "source_split": "NCT_CRC_HE_100K_NONORM_TUM_confirmation",
                "source_record_index": len(rows),
                "sample_id": f"nct_nonorm_tum_s{shard_idx}_{taken:04d}",
                "stream_shard": shard,
                "stream_local_seen_index": int(local_idx),
                "image_path": "",
                "label": 8,
                "label_name": LABEL_NAMES[8],
            } | feats
            rows.append(row)
            taken += 1
            if taken >= args.per_shard:
                break
        if taken < args.per_shard:
            raise RuntimeError(f"Only collected {taken} examples from {shard}")

    df = pd.DataFrame(rows)
    tissue_delta = np.sqrt(((df[TISSUE_COLS] - ref_tissue_median) ** 2).sum(axis=1))
    df["axis_nct_tissue_fraction_similarity"] = -tissue_delta.astype(float)
    levels, thresholds = assign_similarity_levels(df["axis_nct_tissue_fraction_similarity"], args.levels)
    df["level_nct_tissue_fraction_proximity"] = levels
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    summary = []
    for level, part in df.groupby("level_nct_tissue_fraction_proximity", sort=True):
        summary.append(
            {
                "level": int(level),
                "n": int(len(part)),
                "axis_mean": float(part["axis_nct_tissue_fraction_similarity"].mean()),
                "axis_min": float(part["axis_nct_tissue_fraction_similarity"].min()),
                "axis_max": float(part["axis_nct_tissue_fraction_similarity"].max()),
            }
        )
    ledger = json.loads(args.axis_ledger.read_text())
    ledger.setdefault("outcome_informed_hypotheses", {})["tum_tissue_fraction_confirmation"] = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "frozen_before_confirmation_target_scoring",
        "discovery_source": "CRC-VAL all-scored evidence showed TUM recall decreased across the predeclared NCT tissue-fraction proximity axis",
        "hypothesis": "For true colorectal adenocarcinoma epithelium ROI patches, CONCH zero-shot TUM recall decreases as prospective tissue/white/dark/saturation fraction similarity to the NCT reference decreases.",
        "confirmation_dataset": "NCT-CRC-HE-100K-NONORM streamed TUM shards from the public HF/Zenodo mirror",
        "inclusion_criteria": "label 8/TUM patches from three NONORM TUM shards; label defines the class-localized claim boundary, not the split levels",
        "axis_col": "axis_nct_tissue_fraction_similarity",
        "level_col": "level_nct_tissue_fraction_proximity",
        "level_rule": "six equal-frequency bins over the confirmation panel; level 1 is highest NCT tissue-fraction similarity and level 6 is lowest",
        "threshold_quantiles_ascending": thresholds,
        "level_summary_before_scoring": summary,
        "split_membership_uses_target_model": False,
        "split_membership_uses_prediction_errors": False,
        "confirmation_sample_size": int(len(df)),
        "success_criterion": "TUM recall shows a monotone, threshold, or large localized drop as level increases; fixed feature baselines and target CONCH are reported by the same frozen levels.",
        "limitations": "Confirmation data are fresh relative to CRC-VAL discovery but not an independent hospital/site cohort; NONORM patches share the public Kather/NCT source family.",
    }
    args.axis_ledger.write_text(json.dumps(ledger, indent=2))
    print(json.dumps(ledger["outcome_informed_hypotheses"]["tum_tissue_fraction_confirmation"], indent=2), flush=True)
    if args.force_exit:
        os._exit(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
