#!/usr/bin/env python3
"""Freeze an expanded TUM/tissue-fraction confirmation panel.

This expansion keeps the original prospective axis definition and excludes the
already-scored confirmation rows before any new target-model scoring.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import load_dataset

from build_crc_candidate_table import HF_BASE, LABEL_NAMES, image_features
from build_tum_confirmation_panel import TISSUE_COLS, assign_similarity_levels


NONORM_TUM_EXPANSION_SHARDS = [
    "data/NCT_CRC_HE_100K_NONORM-00017-of-00031-185be2828f60b3a7.parquet",
    "data/NCT_CRC_HE_100K_NONORM-00018-of-00031-20db16691204a5c6.parquet",
    "data/NCT_CRC_HE_100K_NONORM-00019-of-00031-9be5fae292c61245.parquet",
    "data/NCT_CRC_HE_100K_NONORM-00020-of-00031-cf3901477d5683dd.parquet",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nct-reference", type=Path, default=Path("spectra_ready_dataset/nct_reference_features.csv"))
    ap.add_argument("--previous-panel", type=Path, default=Path("spectra_ready_dataset/tum_confirmation_panel.csv"))
    ap.add_argument("--out", type=Path, default=Path("spectra_ready_dataset/tum_expansion_panel.csv"))
    ap.add_argument("--diagnostics", type=Path, default=Path("artifacts/tum_expansion/panel_diagnostics.json"))
    ap.add_argument("--axis-ledger", type=Path, default=Path("axis_ledger.json"))
    ap.add_argument("--per-shard", type=int, default=1000)
    ap.add_argument("--levels", type=int, default=10)
    args = ap.parse_args()

    ref = pd.read_csv(args.nct_reference)
    previous = pd.read_csv(args.previous_panel)
    ref_tissue_median = ref[TISSUE_COLS].median()
    used_stream_keys = {
        (row.stream_shard, int(row.stream_local_seen_index))
        for row in previous.itertuples(index=False)
    }
    previous_md5 = set(previous["image_md5"].dropna().astype(str))
    previous_dhash = set(previous["dhash64"].dropna().astype(str))

    rows = []
    internal_md5 = set()
    skipped = {"previous_stream_key": 0, "previous_md5": 0, "internal_md5": 0}
    dhash_overlap_with_previous = 0

    for shard_idx, shard in enumerate(NONORM_TUM_EXPANSION_SHARDS):
        ds = load_dataset("parquet", data_files=HF_BASE + shard, split="train", streaming=True)
        taken = 0
        seen = 0
        for local_idx, ex in enumerate(ds):
            seen += 1
            if int(ex["label"]) != 8:
                continue
            stream_key = (shard, int(local_idx))
            if stream_key in used_stream_keys:
                skipped["previous_stream_key"] += 1
                continue
            feats = image_features(ex["image"])
            image_md5 = str(feats["image_md5"])
            if image_md5 in previous_md5:
                skipped["previous_md5"] += 1
                continue
            if image_md5 in internal_md5:
                skipped["internal_md5"] += 1
                continue
            internal_md5.add(image_md5)
            if str(feats["dhash64"]) in previous_dhash:
                dhash_overlap_with_previous += 1
            rows.append(
                {
                    "source_split": "NCT_CRC_HE_100K_NONORM_TUM_expansion",
                    "source_record_index": len(rows),
                    "sample_id": f"nct_nonorm_tum_exp_s{shard_idx}_{taken:04d}",
                    "stream_shard": shard,
                    "stream_local_seen_index": int(local_idx),
                    "image_path": "",
                    "label": 8,
                    "label_name": LABEL_NAMES[8],
                }
                | feats
            )
            taken += 1
            if taken >= args.per_shard:
                break
        if taken < args.per_shard:
            raise RuntimeError(f"Only collected {taken} unused TUM examples from {shard} after seeing {seen}")

    df = pd.DataFrame(rows)
    tissue_delta = np.sqrt(((df[TISSUE_COLS] - ref_tissue_median) ** 2).sum(axis=1))
    df["axis_nct_tissue_fraction_similarity"] = -tissue_delta.astype(float)
    levels, thresholds = assign_similarity_levels(df["axis_nct_tissue_fraction_similarity"], args.levels)
    df["level_nct_tissue_fraction_proximity"] = levels
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)

    level_summary = []
    feature_cols = TISSUE_COLS + ["gray_mean", "gray_std", "gray_entropy", "edge_mean"]
    for level, part in df.groupby("level_nct_tissue_fraction_proximity", sort=True):
        level_summary.append(
            {
                "level": int(level),
                "n": int(len(part)),
                "axis_mean": float(part["axis_nct_tissue_fraction_similarity"].mean()),
                "axis_min": float(part["axis_nct_tissue_fraction_similarity"].min()),
                "axis_max": float(part["axis_nct_tissue_fraction_similarity"].max()),
                **{f"{col}_mean": float(part[col].mean()) for col in feature_cols},
            }
        )

    diagnostics = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "panel": str(args.out),
        "n": int(len(df)),
        "levels": int(args.levels),
        "per_shard": int(args.per_shard),
        "shards": NONORM_TUM_EXPANSION_SHARDS,
        "excluded_previous_panel_rows": int(len(previous)),
        "skipped": skipped,
        "exact_md5_duplicates_internal": int(df["image_md5"].duplicated().sum()),
        "exact_md5_overlap_with_previous": int(df["image_md5"].isin(previous_md5).sum()),
        "dhash64_overlap_with_previous": int(dhash_overlap_with_previous),
        "level_summary_before_scoring": level_summary,
        "similarity_decreases_by_level_mean": bool(
            all(
                level_summary[i]["axis_mean"] > level_summary[i + 1]["axis_mean"]
                for i in range(len(level_summary) - 1)
            )
        ),
    }
    args.diagnostics.parent.mkdir(parents=True, exist_ok=True)
    args.diagnostics.write_text(json.dumps(diagnostics, indent=2))

    ledger = json.loads(args.axis_ledger.read_text())
    ledger.setdefault("outcome_informed_hypotheses", {})["tum_tissue_fraction_expansion"] = {
        "created_utc": diagnostics["created_utc"],
        "status": "frozen_before_expansion_target_scoring",
        "parent_hypothesis": "tum_tissue_fraction_confirmation",
        "purpose": "Densify and expand the same prospective TUM tissue-fraction axis after the six-level confirmation showed a low-similarity tail drop.",
        "axis_col": "axis_nct_tissue_fraction_similarity",
        "level_col": "level_nct_tissue_fraction_proximity",
        "level_rule": f"{args.levels} equal-frequency bins over an unused expansion panel; level 1 is highest NCT tissue-fraction similarity and level {args.levels} is lowest",
        "features": TISSUE_COLS,
        "direction": "performance is assessed as axis_nct_tissue_fraction_similarity decreases and level increases",
        "confirmation_dataset": "Unused NCT-CRC-HE-100K-NONORM TUM rows from public TUM shards 00017-00020",
        "exclusion_rule": "Exclude all prior confirmation stream keys and exact decoded-image MD5 matches before target-model scoring.",
        "threshold_quantiles_ascending": thresholds,
        "level_summary_before_scoring": level_summary,
        "split_membership_uses_target_model": False,
        "split_membership_uses_prediction_errors": False,
        "split_membership_uses_target_confidence": False,
        "confirmation_sample_size": int(len(df)),
        "success_criterion": "The expanded panel supports a monotone, threshold, or practically large localized TUM-recall drop in the lowest similarity tail, with fixed feature baselines reported on the same frozen levels.",
        "limitations": "Still same public Kather/NCT source family rather than an independent hospital/site cohort.",
    }
    args.axis_ledger.write_text(json.dumps(ledger, indent=2))
    print(json.dumps(diagnostics, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
