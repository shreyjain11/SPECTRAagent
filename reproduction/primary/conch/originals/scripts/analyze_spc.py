#!/usr/bin/env python3
"""Analyze frozen SPECTRA axes, target CONCH results, and fixed baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler


LABELS = list(range(9))
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
    return [c for c in df.columns if c not in FEATURE_EXCLUDE and pd.api.types.is_numeric_dtype(df[c])]


def nearest_centroid_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
    centroids = []
    for lab in LABELS:
        centroids.append(x_train[y_train == lab].mean(axis=0))
    centroids = np.vstack(centroids)
    d2 = ((x_test[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    return d2.argmin(axis=1)


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }


def metric_by_level(df: pd.DataFrame, level_col: str, pred_col: str) -> list[dict]:
    rows = []
    for level, part in df.groupby(level_col, sort=True):
        y = part["label"].to_numpy()
        p = part[pred_col].to_numpy()
        m = metrics(y, p)
        row = {
            "level": int(level),
            "n": int(len(part)),
            "axis_mean": float(part[df.attrs["axis_col"]].mean()),
            **m,
            "label_counts": {str(k): int(v) for k, v in part["label_name"].value_counts().sort_index().to_dict().items()},
        }
        rows.append(row)
    return rows


def per_class_recalls(df: pd.DataFrame, level_col: str, pred_col: str) -> list[dict]:
    rows = []
    for level, part in df.groupby(level_col, sort=True):
        for lab in LABELS:
            sub = part[part["label"] == lab]
            if len(sub) == 0:
                recall = np.nan
            else:
                recall = float((sub[pred_col] == lab).mean())
            rows.append({"level": int(level), "label": lab, "label_name": LABEL_NAMES[lab], "n": int(len(sub)), "recall": recall})
    return rows


def class_adjusted_residual_by_level(df: pd.DataFrame, level_col: str, pred_col: str) -> list[dict]:
    correct = (df[pred_col].to_numpy() == df["label"].to_numpy()).astype(float)
    tmp = df[["label", level_col]].copy()
    tmp["correct"] = correct
    class_mean = tmp.groupby("label")["correct"].transform("mean")
    tmp["residual"] = tmp["correct"] - class_mean
    rows = []
    for level, part in tmp.groupby(level_col, sort=True):
        rows.append(
            {
                "level": int(level),
                "n": int(len(part)),
                "mean_class_adjusted_correct_residual": float(part["residual"].mean()),
            }
        )
    return rows


def stable_class_macro(df: pd.DataFrame, level_col: str, pred_col: str, min_support: int = 10) -> dict:
    stable = []
    for lab in LABELS:
        supports = [int(((df[level_col] == level) & (df["label"] == lab)).sum()) for level in sorted(df[level_col].unique())]
        if min(supports) >= min_support:
            stable.append(lab)
    rows = []
    for level, part in df.groupby(level_col, sort=True):
        recalls = []
        supports = {}
        for lab in stable:
            sub = part[part["label"] == lab]
            supports[LABEL_NAMES[lab]] = int(len(sub))
            recalls.append(float((sub[pred_col] == lab).mean()))
        rows.append(
            {
                "level": int(level),
                "stable_class_macro_recall": float(np.mean(recalls)) if recalls else float("nan"),
                "stable_classes": [LABEL_NAMES[x] for x in stable],
                "supports": supports,
            }
        )
    return {"min_support": min_support, "stable_classes": [LABEL_NAMES[x] for x in stable], "rows": rows}


def assign_deciles(df: pd.DataFrame, axis_col: str) -> pd.Series:
    ranks = df[axis_col].rank(method="first", ascending=False)
    return (pd.qcut(ranks, q=10, labels=False) + 1).astype(int)


def summarize_axis(df: pd.DataFrame, axis_name: str, spec: dict, out_dir: Path) -> dict:
    axis_col = spec["axis_col"]
    level_col = spec["level_col"]
    df = df.copy()
    df.attrs["axis_col"] = axis_col

    target_rows = metric_by_level(df, level_col, "pred")
    centroid_rows = metric_by_level(df, level_col, "baseline_centroid_pred")
    logistic_rows = metric_by_level(df, level_col, "baseline_logistic_pred")
    residual_rows = class_adjusted_residual_by_level(df, level_col, "pred")
    stable_macro = stable_class_macro(df, level_col, "pred", min_support=10)
    target_bacc = [r["balanced_accuracy"] for r in target_rows]
    target_acc = [r["accuracy"] for r in target_rows]
    levels = [r["level"] for r in target_rows]
    rho_bacc = spearmanr(levels, target_bacc).statistic
    rho_acc = spearmanr(levels, target_acc).statistic

    recall_rows = per_class_recalls(df, level_col, "pred")
    pd.DataFrame(recall_rows).to_csv(out_dir / f"{axis_name}_per_class_recalls.csv", index=False)

    decile_summary = None
    if axis_name == "nct_color_texture_proximity":
        decile_col = "level_nct_color_texture_decile"
        df[decile_col] = assign_deciles(df, axis_col)
        df.attrs["axis_col"] = axis_col
        decile_summary = {
            "target": metric_by_level(df, decile_col, "pred"),
            "class_adjusted_residual": class_adjusted_residual_by_level(df, decile_col, "pred"),
            "stable_class_macro_min_support_5": stable_class_macro(df, decile_col, "pred", min_support=5),
        }
        df[["sample_id", axis_col, decile_col]].to_csv(out_dir / "nct_color_texture_decile_assignments.csv", index=False)

    return {
        "axis_col": axis_col,
        "level_col": level_col,
        "target_by_level": target_rows,
        "baseline_centroid_by_level": centroid_rows,
        "baseline_logistic_by_level": logistic_rows,
        "class_adjusted_residual_by_level": residual_rows,
        "stable_class_macro_min_support_10": stable_macro,
        "spearman_level_vs_target_bacc": float(rho_bacc),
        "spearman_level_vs_target_acc": float(rho_acc),
        "decile_densification": decile_summary,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", type=Path, default=Path("spectra_ready_dataset/candidate_features.csv"))
    ap.add_argument("--table", type=Path, default=Path("spectra_ready_dataset/spectra_ready_table.csv"))
    ap.add_argument("--results", type=Path, default=Path("target_model_results.csv"))
    ap.add_argument("--axis-ledger", type=Path, default=Path("axis_ledger.json"))
    ap.add_argument("--out-dir", type=Path, default=Path("artifacts/spc_analysis"))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    all_features = pd.read_csv(args.features, low_memory=False)
    table = pd.read_csv(args.table, low_memory=False)
    results = pd.read_csv(args.results)
    ledger = json.loads(args.axis_ledger.read_text())

    ref = all_features[all_features["source_split"] == "NCT_CRC_HE_100K_reference"].copy()
    crc_features = table.copy()
    merged = crc_features.merge(results, on=["sample_id", "image_path", "label", "label_name"], how="inner")
    if len(merged) != len(table):
        raise RuntimeError(f"Join lost rows: merged={len(merged)} table={len(table)}")

    cols = feature_columns(all_features)
    scaler = StandardScaler()
    x_train = scaler.fit_transform(ref[cols].to_numpy(np.float32))
    y_train = ref["label"].to_numpy()
    x_test = scaler.transform(merged[cols].to_numpy(np.float32))

    merged["baseline_centroid_pred"] = nearest_centroid_predict(x_train, y_train, x_test)
    logreg = LogisticRegression(max_iter=1000, C=1.0, multi_class="auto", solver="lbfgs", random_state=0)
    logreg.fit(x_train, y_train)
    merged["baseline_logistic_pred"] = logreg.predict(x_test)
    merged["baseline_majority_pred"] = 0

    baseline_summary = {
        "centroid": metrics(merged["label"].to_numpy(), merged["baseline_centroid_pred"].to_numpy()),
        "logistic": metrics(merged["label"].to_numpy(), merged["baseline_logistic_pred"].to_numpy()),
        "majority_ADI": metrics(merged["label"].to_numpy(), merged["baseline_majority_pred"].to_numpy()),
        "target_CONCH": metrics(merged["label"].to_numpy(), merged["pred"].to_numpy()),
    }

    axis_summaries = {}
    for axis_name, spec in ledger["axes"].items():
        axis_summaries[axis_name] = summarize_axis(merged, axis_name, spec, args.out_dir)

    merged.to_csv(args.out_dir / "scored_table_with_axes_and_baselines.csv", index=False)
    summary = {
        "n": int(len(merged)),
        "baseline_summary": baseline_summary,
        "axis_summaries": axis_summaries,
    }
    (args.out_dir / "spc_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"n": summary["n"], "baseline_summary": baseline_summary}, indent=2))
    for axis_name, spec in axis_summaries.items():
        print("\\n" + axis_name)
        for row in spec["target_by_level"]:
            print(
                row["level"],
                row["n"],
                f"axis={row['axis_mean']:.4f}",
                f"target_bacc={row['balanced_accuracy']:.4f}",
                f"acc={row['accuracy']:.4f}",
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
