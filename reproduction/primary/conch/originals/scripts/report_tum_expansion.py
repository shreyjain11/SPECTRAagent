#!/usr/bin/env python3
"""Summarize the expanded TUM/tissue-fraction SPC."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return center - half, center + half


def pooled(rows: list[dict], levels: set[int]) -> dict:
    chosen = [r for r in rows if int(r["level"]) in levels]
    n = sum(int(r["n"]) for r in chosen)
    k = sum(round(float(r["tum_recall"]) * int(r["n"])) for r in chosen)
    lo, hi = wilson(k, n)
    return {"levels": sorted(levels), "n": n, "k": k, "recall": k / n, "ci95": [lo, hi]}


def diff_test(a: dict, b: dict) -> dict:
    p1 = a["k"] / a["n"]
    p2 = b["k"] / b["n"]
    diff = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / a["n"] + p2 * (1 - p2) / b["n"])
    ci = [diff - 1.96 * se, diff + 1.96 * se]
    pooled_p = (a["k"] + b["k"]) / (a["n"] + b["n"])
    pooled_se = math.sqrt(pooled_p * (1 - pooled_p) * (1 / a["n"] + 1 / b["n"]))
    z = diff / pooled_se if pooled_se else float("inf")
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"difference": diff, "ci95": ci, "z": z, "p_two_sided_normal": p}


def fmt(x: float) -> str:
    return f"{x:.3f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("."))
    args = ap.parse_args()
    root = args.root

    analysis = json.loads((root / "artifacts/tum_expansion/analysis.json").read_text())
    diagnostics = json.loads((root / "artifacts/tum_expansion/panel_diagnostics.json").read_text())
    previous = json.loads((root / "artifacts/tum_confirmation/analysis.json").read_text())
    panel = pd.read_csv(root / "spectra_ready_dataset/tum_expansion_panel.csv")
    results = pd.read_csv(root / "artifacts/tum_expansion/target_model_results_tum_expansion.csv")
    scored = panel.merge(results, on=["sample_id", "label", "label_name"], how="inner")

    target_rows = analysis["target_by_level"]
    centroid_rows = analysis["baseline_centroid_by_level"]
    logistic_rows = analysis["baseline_logistic_by_level"]
    for rows in (target_rows, centroid_rows, logistic_rows):
        for row in rows:
            n = int(row["n"])
            k = round(float(row["tum_recall"]) * n)
            row["tum_k"] = k
            row["ci95"] = list(wilson(k, n))

    high_1_7 = pooled(target_rows, set(range(1, 8)))
    low_8_10 = pooled(target_rows, {8, 9, 10})
    high_1_6 = pooled(target_rows, set(range(1, 7)))
    transition_7 = pooled(target_rows, {7})
    top_1_3 = pooled(target_rows, {1, 2, 3})
    bottom_8_10 = pooled(target_rows, {8, 9, 10})
    contrast_1_7_vs_8_10 = diff_test(high_1_7, low_8_10)
    contrast_1_6_vs_8_10 = diff_test(high_1_6, low_8_10)
    contrast_top3_vs_bottom3 = diff_test(top_1_3, bottom_8_10)

    level_df = pd.DataFrame(target_rows)
    spearman = float(level_df["level"].corr(level_df["tum_recall"], method="spearman"))
    feature_cols = [
        "tissue_fraction",
        "white_fraction",
        "dark_fraction",
        "saturation_high_fraction",
        "gray_mean",
    ]
    feature_by_level = (
        scored.groupby("level_nct_tissue_fraction_proximity", sort=True)[feature_cols]
        .mean()
        .reset_index()
        .rename(columns={"level_nct_tissue_fraction_proximity": "level"})
        .to_dict(orient="records")
    )

    low_tail = scored[scored["level_nct_tissue_fraction_proximity"].isin([8, 9, 10])]
    high_tail = scored[scored["level_nct_tissue_fraction_proximity"].isin(range(1, 8))]
    exploratory_error_counts = {
        "high_1_7_non_tum_predictions": high_tail.loc[high_tail["pred_label_name"] != "TUM", "pred_label_name"].value_counts().to_dict(),
        "low_8_10_non_tum_predictions": low_tail.loc[low_tail["pred_label_name"] != "TUM", "pred_label_name"].value_counts().to_dict(),
    }

    metrics = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "validity_decision": "valid_for_localized_public_crc_tum_tail_boundary__weak_for_independent_site_generalization",
        "n": analysis["n"],
        "frozen_panel": diagnostics,
        "target_overall_tum_recall": analysis["target_overall_tum_recall"],
        "baseline_centroid_overall_tum_recall": analysis["baseline_centroid_overall_tum_recall"],
        "baseline_logistic_overall_tum_recall": analysis["baseline_logistic_overall_tum_recall"],
        "spearman_level_vs_target_tum_recall": spearman,
        "target_by_level": target_rows,
        "baseline_centroid_by_level": centroid_rows,
        "baseline_logistic_by_level": logistic_rows,
        "pooled_target": {
            "high_1_7": high_1_7,
            "low_8_10": low_8_10,
            "high_1_6": high_1_6,
            "transition_7": transition_7,
            "top_1_3": top_1_3,
            "bottom_8_10": bottom_8_10,
        },
        "contrasts": {
            "levels_1_7_minus_8_10": contrast_1_7_vs_8_10,
            "levels_1_6_minus_8_10": contrast_1_6_vs_8_10,
            "levels_1_3_minus_8_10": contrast_top3_vs_bottom3,
        },
        "feature_by_level": feature_by_level,
        "previous_confirmation_target_by_level": previous["target_by_level"],
        "exploratory_error_counts": exploratory_error_counts,
    }

    out_dir = root / "artifacts/tum_expansion"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "expanded_metrics.json").write_text(json.dumps(metrics, indent=2))

    table_lines = [
        "| Level | n | Axis Mean | CONCH TUM Recall | 95% CI | Centroid | Logistic | Dark Mean | Sat-High Mean |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    feat_by_level = {int(r["level"]): r for r in feature_by_level}
    for t, c, l in zip(target_rows, centroid_rows, logistic_rows):
        level = int(t["level"])
        ci = t["ci95"]
        feat = feat_by_level[level]
        table_lines.append(
            f"| {level} | {int(t['n'])} | {fmt(float(t['axis_mean']))} | "
            f"{fmt(float(t['tum_recall']))} | [{fmt(ci[0])}, {fmt(ci[1])}] | "
            f"{fmt(float(c['tum_recall']))} | {fmt(float(l['tum_recall']))} | "
            f"{fmt(float(feat['dark_fraction']))} | {fmt(float(feat['saturation_high_fraction']))} |"
        )

    report = f"""# CONCH TUM Tissue/Stain-Fraction SPC Expansion

## Status

This expansion strengthens the prior localized finding. The same prospective axis was kept frozen before target scoring: Euclidean distance in tissue, white, dark, and high-saturation pixel fractions from the class-balanced NCT reference median, with higher numbered levels meaning lower similarity.

The expanded panel used 4,000 unused NCT-CRC-HE-100K-NONORM TUM images, 400 per frozen level. It excluded all 1,800 previously scored confirmation rows by stream key and exact decoded-image MD5. Internal exact MD5 duplicates were 0, exact overlap with the previous panel was 0, and dHash64 overlap with the previous panel was 0. Mean measured similarity decreased across all 10 levels.

Validity decision: `valid` for the bounded public CRC ROI TUM low-similarity tail boundary; `weak` for independent-site or deployment generalization because all confirmation evidence is still from the public Kather/NCT source family.

## Expanded Curve

{chr(10).join(table_lines)}

## Main Contrast

Levels 1-7 stayed high overall: {high_1_7['k']}/{high_1_7['n']} = {fmt(high_1_7['recall'])} TUM recall, 95% CI [{fmt(high_1_7['ci95'][0])}, {fmt(high_1_7['ci95'][1])}].

Levels 8-10 formed the low-similarity tail: {low_8_10['k']}/{low_8_10['n']} = {fmt(low_8_10['recall'])} TUM recall, 95% CI [{fmt(low_8_10['ci95'][0])}, {fmt(low_8_10['ci95'][1])}].

Difference, levels 1-7 minus 8-10: {fmt(contrast_1_7_vs_8_10['difference'])}, 95% CI [{fmt(contrast_1_7_vs_8_10['ci95'][0])}, {fmt(contrast_1_7_vs_8_10['ci95'][1])}], two-sided normal p ~= {contrast_1_7_vs_8_10['p_two_sided_normal']:.2e}.

The curve is threshold-shaped rather than strictly monotone: levels 8-10 are consistently degraded, but level 9 and 10 rebound slightly relative to level 8. Spearman level-vs-recall over the 10 frozen bins is {fmt(spearman)}.

## Baseline Comparison

CONCH overall TUM recall on the expansion panel was {fmt(analysis['target_overall_tum_recall'])}. Fixed feature baselines were much lower: centroid {fmt(analysis['baseline_centroid_overall_tum_recall'])}, logistic {fmt(analysis['baseline_logistic_overall_tum_recall'])}. The baselines also degrade strongly in the low-similarity tail, which supports the axis as a real prospective image-distribution shift rather than a CONCH-confidence artifact.

## Interpretation

The low-similarity tail is not simply low tissue area. In the expanded panel it is mainly a dark/high-saturation stain tail: mean dark fraction rises from {fmt(float(feat_by_level[1]['dark_fraction']))} at level 1 to {fmt(float(feat_by_level[10]['dark_fraction']))} at level 10, and high-saturation fraction rises from {fmt(float(feat_by_level[1]['saturation_high_fraction']))} to {fmt(float(feat_by_level[10]['saturation_high_fraction']))}.

Exploratory failure characterization, not an axis definition: in levels 8-10, non-TUM predictions were mostly STR, MUC, DEB, and BACK. This was computed after target scoring and should not be used as confirmatory split logic.

## Relation To Previous Confirmation

The earlier six-level confirmation had TUM recall [0.903, 0.930, 0.930, 0.883, 0.697, 0.730]. The expanded 10-level panel reproduces the same low-tail shape with more examples per level: levels 8-10 were [0.640, 0.700, 0.703].

## Artifacts

- `spectra_ready_dataset/tum_expansion_panel.csv`
- `artifacts/tum_expansion/panel_diagnostics.json`
- `artifacts/tum_expansion/target_model_results_tum_expansion.csv`
- `artifacts/tum_expansion/analysis.json`
- `artifacts/tum_expansion/expanded_metrics.json`
"""
    (out_dir / "expanded_finding_report.md").write_text(report)

    ledger_path = root / "axis_ledger.json"
    ledger = json.loads(ledger_path.read_text())
    entry = ledger.setdefault("outcome_informed_hypotheses", {}).setdefault("tum_tissue_fraction_expansion", {})
    entry["status"] = "expanded_scored_and_analyzed"
    entry["analysis_artifacts"] = [
        "artifacts/tum_expansion/analysis.json",
        "artifacts/tum_expansion/expanded_metrics.json",
        "artifacts/tum_expansion/expanded_finding_report.md",
    ]
    entry["validity_decision"] = metrics["validity_decision"]
    entry["target_curve_by_level"] = [
        {"level": int(r["level"]), "n": int(r["n"]), "tum_recall": float(r["tum_recall"])}
        for r in target_rows
    ]
    entry["main_contrast_levels_1_7_minus_8_10"] = contrast_1_7_vs_8_10
    ledger_path.write_text(json.dumps(ledger, indent=2))

    print(json.dumps(metrics["pooled_target"], indent=2), flush=True)
    print(str(out_dir / "expanded_finding_report.md"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
