#!/usr/bin/env python3
"""Analyze the frozen TUM confirmation SPC and fixed baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from analyze_spc import LABELS, LABEL_NAMES, feature_columns, nearest_centroid_predict


def by_level(df: pd.DataFrame, pred_col: str) -> list[dict]:
    rows = []
    for level, part in df.groupby("level_nct_tissue_fraction_proximity", sort=True):
        rows.append(
            {
                "level": int(level),
                "n": int(len(part)),
                "axis_mean": float(part["axis_nct_tissue_fraction_similarity"].mean()),
                "tum_recall": float((part[pred_col] == 8).mean()),
                "prediction_counts": {LABEL_NAMES[int(k)]: int(v) for k, v in part[pred_col].value_counts().sort_index().items()},
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", type=Path, default=Path("spectra_ready_dataset/candidate_features.csv"))
    ap.add_argument("--panel", type=Path, default=Path("spectra_ready_dataset/tum_confirmation_panel.csv"))
    ap.add_argument("--results", type=Path, default=Path("artifacts/tum_confirmation/target_model_results_tum_confirmation.csv"))
    ap.add_argument("--out", type=Path, default=Path("artifacts/tum_confirmation/analysis.json"))
    args = ap.parse_args()

    all_features = pd.read_csv(args.features, low_memory=False)
    ref = all_features[all_features["source_split"] == "NCT_CRC_HE_100K_reference"].copy()
    panel = pd.read_csv(args.panel, low_memory=False)
    results = pd.read_csv(args.results)
    df = panel.merge(results, on=["sample_id", "label", "label_name"], how="inner")
    if len(df) != len(panel):
        raise RuntimeError(f"Join lost rows: {len(df)} vs {len(panel)}")

    cols = feature_columns(all_features)
    scaler = StandardScaler()
    x_train = scaler.fit_transform(ref[cols].to_numpy(np.float32))
    y_train = ref["label"].to_numpy()
    x_test = scaler.transform(df[cols].to_numpy(np.float32))
    df["baseline_centroid_pred"] = nearest_centroid_predict(x_train, y_train, x_test)
    logreg = LogisticRegression(max_iter=1000, C=1.0, solver="lbfgs", random_state=0)
    logreg.fit(x_train, y_train)
    df["baseline_logistic_pred"] = logreg.predict(x_test)

    analysis = {
        "n": int(len(df)),
        "target_overall_tum_recall": float((df["pred"] == 8).mean()),
        "baseline_centroid_overall_tum_recall": float((df["baseline_centroid_pred"] == 8).mean()),
        "baseline_logistic_overall_tum_recall": float((df["baseline_logistic_pred"] == 8).mean()),
        "target_by_level": by_level(df, "pred"),
        "baseline_centroid_by_level": by_level(df, "baseline_centroid_pred"),
        "baseline_logistic_by_level": by_level(df, "baseline_logistic_pred"),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(analysis, indent=2))
    df.to_csv(args.out.parent / "scored_tum_confirmation_with_baselines.csv", index=False)
    print(json.dumps(analysis, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
