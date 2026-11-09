#!/usr/bin/env python3
"""Freeze prospective SPECTRA axes before target-model scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


FEATURE_EXCLUDE = {
    "source_split",
    "source_record_index",
    "sample_id",
    "image_path",
    "label",
    "label_name",
    "reference_shard",
    "image_md5",
    "dhash64",
}


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in df.columns:
        if col in FEATURE_EXCLUDE:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)
    return cols


def zscore(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mu = train.mean(axis=0)
    sd = train.std(axis=0)
    sd[sd < 1e-6] = 1.0
    return (train - mu) / sd, (test - mu) / sd, mu, sd


def mean_knn_distance(test: np.ndarray, ref: np.ndarray, k: int = 20, chunk: int = 512) -> np.ndarray:
    k = min(k, ref.shape[0])
    out = np.empty(test.shape[0], dtype=np.float32)
    ref_sq = np.sum(ref * ref, axis=1)[None, :]
    for start in range(0, test.shape[0], chunk):
        x = test[start : start + chunk]
        d2 = np.sum(x * x, axis=1)[:, None] + ref_sq - 2.0 * (x @ ref.T)
        d2 = np.maximum(d2, 0.0)
        part = np.partition(np.sqrt(d2), kth=k - 1, axis=1)[:, :k]
        out[start : start + chunk] = part.mean(axis=1)
    return out


def assign_similarity_levels(values: pd.Series, n_levels: int) -> tuple[pd.Series, list[float]]:
    """Assign 1=highest similarity through n=lowest similarity by quantile."""
    ranks = values.rank(method="first", ascending=False)
    levels = pd.qcut(ranks, q=n_levels, labels=False) + 1
    quantiles = [float(values.quantile(q)) for q in np.linspace(0, 1, n_levels + 1)]
    return levels.astype(int), quantiles


def level_summary(df: pd.DataFrame, axis_col: str, level_col: str) -> list[dict]:
    rows = []
    for level, part in df.groupby(level_col, sort=True):
        label_counts = part["label_name"].value_counts().sort_index().to_dict()
        rows.append(
            {
                "level": int(level),
                "n": int(len(part)),
                "axis_mean": float(part[axis_col].mean()),
                "axis_min": float(part[axis_col].min()),
                "axis_max": float(part[axis_col].max()),
                "label_counts": {str(k): int(v) for k, v in label_counts.items()},
            }
        )
    return rows


def monotone_decreasing(summary: list[dict]) -> bool:
    means = [row["axis_mean"] for row in summary]
    return all(a >= b for a, b in zip(means, means[1:]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", type=Path, default=Path("spectra_ready_dataset/candidate_features.csv"))
    ap.add_argument("--out-table", type=Path, default=Path("spectra_ready_dataset/spectra_ready_table.csv"))
    ap.add_argument("--axis-ledger", type=Path, default=Path("axis_ledger.json"))
    ap.add_argument("--state", type=Path, default=Path("spectra_loop_state.json"))
    ap.add_argument("--levels", type=int, default=6)
    args = ap.parse_args()

    df = pd.read_csv(args.features)
    crc = df[df["source_split"] == "CRC_VAL_HE_7K"].copy().reset_index(drop=True)
    ref = df[df["source_split"] == "NCT_CRC_HE_100K_reference"].copy().reset_index(drop=True)
    cols_all = feature_columns(df)
    color_cols = [
        c
        for c in cols_all
        if c.startswith(("r_", "g_", "b_", "h_", "s_", "v_", "gray_hist_", "gray_mean", "gray_std"))
    ]
    tissue_cols = ["tissue_fraction", "white_fraction", "dark_fraction", "saturation_high_fraction"]
    texture_cols = ["gray_entropy", "edge_mean", "edge_std", "gray_std"]

    ref_z, crc_z, _, _ = zscore(ref[cols_all].to_numpy(np.float32), crc[cols_all].to_numpy(np.float32))
    ref_color_z, crc_color_z, _, _ = zscore(
        ref[color_cols].to_numpy(np.float32), crc[color_cols].to_numpy(np.float32)
    )

    crc["axis_nct_color_texture_similarity"] = -mean_knn_distance(crc_z, ref_z, k=20)
    crc["axis_nct_color_similarity"] = -mean_knn_distance(crc_color_z, ref_color_z, k=20)

    ref_tissue_median = ref[tissue_cols].median()
    tissue_delta = np.sqrt(((crc[tissue_cols] - ref_tissue_median) ** 2).sum(axis=1))
    crc["axis_nct_tissue_fraction_similarity"] = -tissue_delta.astype(float)

    ref_texture_median = ref[texture_cols].median()
    texture_delta = np.sqrt(((crc[texture_cols] - ref_texture_median) ** 2).sum(axis=1))
    crc["axis_nct_texture_complexity_similarity"] = -texture_delta.astype(float)

    axes = {
        "nct_color_texture_proximity": {
            "axis_col": "axis_nct_color_texture_similarity",
            "level_col": "level_nct_color_texture_proximity",
            "direction": "higher score means more similar to a class-balanced NCT-CRC-HE-100K color/texture reference; SPC is read as level increases and similarity decreases",
            "feature_family": "RGB/HSV/intensity histograms, tissue fraction, and edge/entropy features",
            "primary": True,
        },
        "nct_color_proximity": {
            "axis_col": "axis_nct_color_similarity",
            "level_col": "level_nct_color_proximity",
            "direction": "higher score means more similar to the NCT reference in color/stain statistics only",
            "feature_family": "RGB/HSV/intensity summary and histogram features",
            "primary": False,
        },
        "nct_tissue_fraction_proximity": {
            "axis_col": "axis_nct_tissue_fraction_similarity",
            "level_col": "level_nct_tissue_fraction_proximity",
            "direction": "higher score means tissue/white/dark/saturation fractions closer to NCT reference median",
            "feature_family": "tissue, white, dark, and high-saturation fractions",
            "primary": False,
        },
        "nct_texture_complexity_proximity": {
            "axis_col": "axis_nct_texture_complexity_similarity",
            "level_col": "level_nct_texture_complexity_proximity",
            "direction": "higher score means edge and intensity-entropy statistics closer to NCT reference median",
            "feature_family": "edge mean/std, gray std, gray entropy",
            "primary": False,
        },
    }

    ledger_axes = {}
    for name, spec in axes.items():
        levels, thresholds = assign_similarity_levels(crc[spec["axis_col"]], args.levels)
        crc[spec["level_col"]] = levels
        summary = level_summary(crc, spec["axis_col"], spec["level_col"])
        ledger_axes[name] = {
            **spec,
            "status": "frozen_before_target_scoring",
            "unit": "224x224 H&E ROI image patch",
            "n_levels": int(args.levels),
            "level_rule": f"equal-frequency quantile bins over CRC-VAL by {spec['axis_col']}; level 1 is highest similarity",
            "threshold_quantiles_ascending": thresholds,
            "level_summary_before_scoring": summary,
            "measured_similarity_decreases": monotone_decreasing(summary),
            "split_membership_uses_target_model": False,
            "split_membership_uses_heldout_labels": False,
            "predeclared_metric": "balanced accuracy by level, with accuracy, macro F1, per-class support, fixed baselines, and class-composition controls",
            "success_criterion": "claim-supporting only if target balanced accuracy shows an interpretable monotone, threshold, or localized degradation as similarity decreases, not materially explained by class composition or fixed baselines",
        }

    crc.to_csv(args.out_table, index=False)
    ledger = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "paper_reference": "/home/unix/yektefai/.cache/spectra/runs/conch_generalizability_audit_20260603/source/CONCH/README.md",
        "model": "MahmoodLab/conch conch_ViT-B-16, source commit 141cc09c7d4ff33d8eda562bd75169b457f71a62",
        "dataset": "CRC-VAL-HE-7K from 1aurent/NCT-CRC-HE mirror of Zenodo 10.5281/zenodo.1214456; NCT-CRC-HE-100K streamed only for class-balanced prospective reference features",
        "target_scoring_status": "not_started",
        "duplicate_policy": "exact MD5 and 64-bit dHash diagnostics computed; exact duplicate target images are retained only if unique in CRC-VAL, otherwise flagged before scoring",
        "axes": ledger_axes,
    }
    args.axis_ledger.write_text(json.dumps(ledger, indent=2))

    state = {
        "phase": "axes_frozen_before_target_scoring",
        "spectra_ready_table": str(args.out_table),
        "axis_ledger": str(args.axis_ledger),
        "crc_val_rows": int(len(crc)),
        "nct_reference_rows": int(len(ref)),
        "feature_columns_all_count": len(cols_all),
        "feature_columns_color_count": len(color_cols),
        "candidate_axes": list(axes.keys()),
        "next_step": "download/load CONCH checkpoint and score all CRC-VAL rows once",
    }
    args.state.write_text(json.dumps(state, indent=2))
    print(json.dumps(state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
