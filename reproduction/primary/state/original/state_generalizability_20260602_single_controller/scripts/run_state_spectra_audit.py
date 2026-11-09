import ast
import json
import math
import os
import re
import tomllib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from huggingface_hub import HfApi, hf_hub_download
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "hf_cache" / "hub"
ART = ROOT / "artifacts"
SPECTRA = ROOT / "spectra_ready_dataset"
STATE = ROOT / "external" / "state"

os.environ.setdefault("HF_HOME", str(ROOT / "hf_cache"))
os.environ.setdefault("HF_HUB_CACHE", str(CACHE))

MODEL_REPOS = [
    "arcinstitute/ST-HVG-Tahoe",
    "arcinstitute/ST-SE-Tahoe",
    "arcinstitute/ST-HVG-Replogle",
    "arcinstitute/ST-SE-Replogle",
    "arcinstitute/ST-HVG-Parse",
    "arcinstitute/ST-SE-Parse",
]

PRIMARY_METRICS = [
    "overlap_at_N",
    "de_sig_genes_recall",
    "de_spearman_lfc_sig",
    "pearson_delta",
    "mse_delta",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm_name(x: str) -> str:
    x = str(x).strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x


def loose_name(x: str) -> str:
    x = norm_name(x)
    x = re.sub(r"\([^)]*\)", "", x)
    x = re.sub(
        r"\b(hydrochloride|hydrate|monohydrate|dihydrate|trihydrate|mesylate|maleate|tosylate|sodium|calcium|potassium|phosphate|sulfate|citrate|acetate|hemihydrate|salt|solvate|tf)\b",
        "",
        x,
    )
    x = re.sub(r"[^a-z0-9]+", "", x)
    return x


def canonical_context_name(x: str) -> str:
    return str(x).strip().replace("/", "-")


def parse_perturbation(value: str):
    """Parse STATE perturbation strings into name/dose/unit when possible."""
    if not isinstance(value, str):
        return None, np.nan, None
    s = value.strip()
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, list) and obj and isinstance(obj[0], tuple):
            tup = obj[0]
            name = str(tup[0]).strip()
            dose = float(tup[1]) if len(tup) > 1 else np.nan
            unit = str(tup[2]) if len(tup) > 2 else None
            return name, dose, unit
    except Exception:
        pass
    return s, np.nan, None


def parse_toml(path: Path):
    with open(path, "rb") as f:
        return tomllib.load(f)


def parse_tahoe_fewshot_toml(path: Path):
    cfg = parse_toml(path)
    out = {}
    for key, spec in cfg.get("fewshot", {}).items():
        context = canonical_context_name(key.split(".", 1)[1])
        parsed = {"val": [], "test": []}
        for split in ["val", "test"]:
            for p in spec.get(split, []):
                name, dose, unit = parse_perturbation(p)
                parsed[split].append(
                    {
                        "perturbation": p,
                        "drug": name,
                        "dose": dose,
                        "unit": unit,
                        "drug_norm": norm_name(name),
                        "drug_loose": loose_name(name),
                    }
                )
        out[context] = parsed
    return out


def get_hf_file_manifest():
    manifest_path = ART / "hf_resource_manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    api = HfApi()
    files = []
    summary = []
    repos = [(r, "model") for r in MODEL_REPOS] + [
        ("arcinstitute/Replogle-Nadig-Preprint", "dataset"),
        ("arcinstitute/State-Parse-Filtered", "dataset"),
        ("tahoebio/Tahoe-100M", "dataset"),
        ("arcinstitute/SE-600M", "model"),
        ("arcinstitute/SE-100M", "model"),
    ]
    for repo, typ in repos:
        rec = {"repo_id": repo, "repo_type": typ, "status": "ok", "total_bytes": 0, "n_files": 0}
        try:
            info = api.model_info(repo, files_metadata=True) if typ == "model" else api.dataset_info(repo, files_metadata=True)
            for sib in info.siblings or []:
                size = getattr(sib, "size", None) or 0
                rec["total_bytes"] += size
                rec["n_files"] += 1
                files.append({"repo_id": repo, "repo_type": typ, "path": sib.rfilename, "size": size})
        except Exception as e:
            rec.update({"status": "error", "error": f"{type(e).__name__}: {str(e)[:300]}"})
        summary.append(rec)
    obj = {"summary": summary, "files": files}
    manifest_path.write_text(json.dumps(obj, indent=2))
    return obj


def result_file_rows(manifest):
    rows = []
    for f in manifest["files"]:
        if f["repo_type"] != "model" or f["repo_id"] not in MODEL_REPOS:
            continue
        p = f["path"]
        if "/eval_best.ckpt/" not in p:
            continue
        if not p.endswith("_results.csv"):
            continue
        if p.endswith("_pred_de.csv") or p.endswith("_real_de.csv") or p.endswith("_agg_results.csv"):
            continue
        rows.append(f)
    return rows


def parse_result_path(repo: str, path: str):
    dataset = "unknown"
    protocol = "unknown"
    context = None
    split_id = None
    representation = "SE" if "ST-SE" in repo else "HVG"
    if "Tahoe" in repo:
        dataset = "Tahoe-100M"
        protocol = "zeroshot" if path.startswith("zeroshot/") else "fewshot"
        context = Path(path).name.replace("_results.csv", "")
    elif "Replogle" in repo:
        dataset = "Replogle-Nadig"
        parts = path.split("/")
        protocol = parts[0]
        context = parts[1]
    elif "Parse" in repo:
        dataset = "Parse-PBMC"
        parts = path.split("/")
        protocol = parts[0]
        split_id = parts[1]
        context = Path(path).name.replace("_results.csv", "")
    return dataset, protocol, context, split_id, representation


def load_target_results(manifest):
    cache_dir = SPECTRA / "loaded_target_results"
    cache_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    download_log = []
    for f in result_file_rows(manifest):
        repo = f["repo_id"]
        path = f["path"]
        local = hf_hub_download(repo_id=repo, filename=path, cache_dir=str(CACHE))
        df = pd.read_csv(local)
        dataset, protocol, context, split_id, rep = parse_result_path(repo, path)
        df.insert(0, "source_repo", repo)
        df.insert(1, "source_path", path)
        df.insert(2, "dataset_family", dataset)
        df.insert(3, "protocol", protocol)
        df.insert(4, "context", context)
        df.insert(5, "split_id", split_id)
        df.insert(6, "representation", rep)
        names, doses, units = zip(*[parse_perturbation(x) for x in df["perturbation"].tolist()])
        df["perturbation_name"] = names
        df["dose"] = doses
        df["dose_unit"] = units
        df["perturbation_norm"] = [norm_name(x) for x in names]
        df["perturbation_loose"] = [loose_name(x) for x in names]
        frames.append(df)
        download_log.append({"repo": repo, "path": path, "rows": int(len(df)), "bytes": f.get("size", 0), "local": local})
    all_df = pd.concat(frames, ignore_index=True)
    all_df.to_csv(ROOT / "target_model_results.csv", index=False)
    (ART / "loaded_target_results_manifest.json").write_text(json.dumps(download_log, indent=2))
    return all_df, download_log


def load_tahoe_metadata():
    drug_path = hf_hub_download(
        repo_id="tahoebio/Tahoe-100M",
        repo_type="dataset",
        filename="metadata/drug_metadata.parquet",
        cache_dir=str(CACHE),
    )
    gene_path = hf_hub_download(
        repo_id="tahoebio/Tahoe-100M",
        repo_type="dataset",
        filename="metadata/gene_metadata.parquet",
        cache_dir=str(CACHE),
    )
    cell_path = hf_hub_download(
        repo_id="tahoebio/Tahoe-100M",
        repo_type="dataset",
        filename="metadata/cell_line_metadata.parquet",
        cache_dir=str(CACHE),
    )
    return pd.read_parquet(drug_path), pd.read_parquet(gene_path), pd.read_parquet(cell_path)


def make_drug_lookup(drug_meta: pd.DataFrame):
    by_norm = {}
    by_loose = {}
    for _, row in drug_meta.iterrows():
        rec = row.to_dict()
        n = norm_name(row["drug"])
        l = loose_name(row["drug"])
        by_norm.setdefault(n, rec)
        by_loose.setdefault(l, rec)
    return by_norm, by_loose


def attach_drug_metadata(df: pd.DataFrame, drug_meta: pd.DataFrame):
    by_norm, by_loose = make_drug_lookup(drug_meta)
    recs = []
    map_status = []
    for _, row in df.iterrows():
        rec = by_norm.get(row["perturbation_norm"])
        status = "exact_norm"
        if rec is None:
            rec = by_loose.get(row["perturbation_loose"])
            status = "loose"
        if rec is None:
            rec = {}
            status = "missing"
        map_status.append(status)
        recs.append(rec)
    meta = pd.DataFrame(recs)
    meta = meta.add_prefix("drugmeta_")
    out = pd.concat([df.reset_index(drop=True), meta.reset_index(drop=True)], axis=1)
    out["drug_metadata_match"] = map_status
    return out


def fingerprint_from_smiles(smiles):
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    return gen.GetFingerprint(mol)


def is_fingerprint(value) -> bool:
    return value is not None and hasattr(value, "GetNumBits")


def compute_context_chemical_axis(tahoe_df: pd.DataFrame, drug_meta: pd.DataFrame):
    toml_path = STATE / "state_preprint_toml_files" / "tahoe_tomls" / "generalization.toml"
    fewshot = parse_tahoe_fewshot_toml(toml_path)
    by_norm, by_loose = make_drug_lookup(drug_meta)
    drug_meta = drug_meta.copy()
    drug_meta["drug_norm"] = drug_meta["drug"].map(norm_name)
    drug_meta["drug_loose"] = drug_meta["drug"].map(loose_name)
    drug_meta["fingerprint"] = drug_meta["canonical_smiles"].map(fingerprint_from_smiles)
    fps_by_norm = {r["drug_norm"]: r["fingerprint"] for _, r in drug_meta.iterrows() if is_fingerprint(r["fingerprint"])}
    fps_by_loose = {r["drug_loose"]: r["fingerprint"] for _, r in drug_meta.iterrows() if is_fingerprint(r["fingerprint"])}

    def find_fp(norm, loose):
        fp = fps_by_norm.get(norm)
        if is_fingerprint(fp):
            return fp
        fp = fps_by_loose.get(loose)
        if is_fingerprint(fp):
            return fp
        return None

    all_drugs = set(drug_meta["drug_norm"])
    context_train = {}
    context_val = {}
    context_test = {}
    for context, spec in fewshot.items():
        val = {x["drug_norm"] for x in spec["val"]}
        test = {x["drug_norm"] for x in spec["test"]}
        context_val[context] = val
        context_test[context] = test
        context_train[context] = all_drugs - val - test

    sim_records = []
    for context, train_norms in context_train.items():
        train_fps = []
        for n in train_norms:
            rec = by_norm.get(n)
            if rec is None:
                continue
            fp = fingerprint_from_smiles(rec.get("canonical_smiles"))
            if fp is not None:
                train_fps.append((n, rec.get("drug"), fp))
        for _, row in tahoe_df[tahoe_df["context"] == context].iterrows():
            fp = find_fp(row["perturbation_norm"], row["perturbation_loose"])
            max_sim = np.nan
            nearest = None
            if is_fingerprint(fp) and train_fps:
                sims = [(DataStructs.TanimotoSimilarity(fp, tfp), n, d) for n, d, tfp in train_fps]
                max_sim, _, nearest = max(sims, key=lambda x: x[0])
            sim_records.append(
                {
                    "row_key": row["row_key"],
                    "target_context_train_drug_count": len(train_norms),
                    "target_context_val_drug_count": len(context_val[context]),
                    "target_context_test_drug_count": len(context_test[context]),
                    "max_tanimoto_to_target_context_train_drug": max_sim,
                    "nearest_target_context_train_drug": nearest,
                }
            )
    sim_df = pd.DataFrame(sim_records)
    out = tahoe_df.merge(sim_df, on="row_key", how="left")

    eligible = out[
        (out["dataset_family"] == "Tahoe-100M")
        & (out["protocol"] == "fewshot")
        & out["max_tanimoto_to_target_context_train_drug"].notna()
    ].copy()
    # Frozen level rule: equal-frequency bins from prospective similarity only, pooled across eligible
    # perturbation-by-context units. This is set before any metric aggregation in this script.
    labels = ["L5_far", "L4_low_mid", "L3_mid", "L2_high_mid", "L1_near"]
    eligible["chem_support_level"] = pd.qcut(
        eligible["max_tanimoto_to_target_context_train_drug"].rank(method="first"),
        q=5,
        labels=labels,
    )
    level_map = eligible[["row_key", "chem_support_level"]]
    out = out.merge(level_map, on="row_key", how="left")
    return out


def summarize_axis(df: pd.DataFrame, axis_col: str, similarity_col: str, subset_name: str):
    rows = []
    sub = df[df[axis_col].notna()].copy()
    order = sorted(sub[axis_col].unique())
    for level in order:
        g = sub[sub[axis_col] == level]
        rec = {
            "subset": subset_name,
            "axis_col": axis_col,
            "level": str(level),
            "n_rows": int(len(g)),
            "n_unique_contexts": int(g["context"].nunique()),
            "n_unique_perturbations": int(g["perturbation_name"].nunique()),
            "n_unique_drug_context_dose": int(
                g[["context", "perturbation_name", "dose"]].drop_duplicates().shape[0]
            ),
            "similarity_mean": float(g[similarity_col].mean()),
            "similarity_min": float(g[similarity_col].min()),
            "similarity_max": float(g[similarity_col].max()),
            "zero_de_baseline_overlap_at_N": 0.0,
            "zero_de_baseline_de_sig_genes_recall": 0.0,
            "zero_de_baseline_de_count_mae": float(g["de_nsig_counts_real"].abs().mean()),
        }
        for m in PRIMARY_METRICS:
            if m in g.columns:
                rec[f"{m}_mean"] = float(g[m].mean())
                rec[f"{m}_median"] = float(g[m].median())
                rec[f"{m}_std"] = float(g[m].std(ddof=1))
        if "de_nsig_counts_pred" in g.columns:
            rec["state_de_count_mae"] = float((g["de_nsig_counts_pred"] - g["de_nsig_counts_real"]).abs().mean())
        rows.append(rec)
    return pd.DataFrame(rows)


def metric_trend(summary: pd.DataFrame, metric: str):
    s = summary[["level", "similarity_mean", f"{metric}_mean"]].copy()
    if len(s) < 3 or s[f"{metric}_mean"].isna().any():
        return {"metric": metric, "status": "insufficient"}
    # Levels are named L5_far ... L1_near. Sort by similarity descending for degradation interpretation.
    s = s.sort_values("similarity_mean", ascending=False)
    x = s["similarity_mean"].to_numpy()
    y = s[f"{metric}_mean"].to_numpy()
    if len(np.unique(x)) < 3:
        return {"metric": metric, "status": "invalid_similarity_degenerate"}
    corr = float(np.corrcoef(x, y)[0, 1])
    near = float(y[0])
    far = float(y[-1])
    delta_far_minus_near = far - near
    return {
        "metric": metric,
        "pearson_level_corr_with_similarity": corr,
        "near_mean": near,
        "far_mean": far,
        "far_minus_near": delta_far_minus_near,
        "relative_far_minus_near": float(delta_far_minus_near / near) if near else np.nan,
    }


def dose_axis(df: pd.DataFrame):
    sub = df[(df["dataset_family"] == "Tahoe-100M") & (df["protocol"] == "fewshot")].copy()
    sub["dose_level"] = sub["dose"].map({0.05: "D1_low_0.05", 0.5: "D2_mid_0.5", 5.0: "D3_high_5.0", 0.0: "D0_control"})
    return sub


def all_scored_axis_discovery(df: pd.DataFrame):
    """Outcome-informed discovery for prospective features only. Does not define final claims."""
    candidates = []
    metric = "overlap_at_N"
    for name, sub in [
        ("tahoe_moa_broad", df[(df["dataset_family"] == "Tahoe-100M") & df.get("drugmeta_moa-broad").notna()]),
        ("tahoe_moa_fine", df[(df["dataset_family"] == "Tahoe-100M") & df.get("drugmeta_moa-fine").notna()]),
        ("tahoe_dose", df[(df["dataset_family"] == "Tahoe-100M") & df["dose"].notna()]),
        ("dataset_family", df[df["dataset_family"].notna()]),
        ("representation", df[df["representation"].notna()]),
    ]:
        if sub.empty:
            continue
        col = {
            "tahoe_moa_broad": "drugmeta_moa-broad",
            "tahoe_moa_fine": "drugmeta_moa-fine",
            "tahoe_dose": "dose",
            "dataset_family": "dataset_family",
            "representation": "representation",
        }[name]
        g = sub.groupby(col)[metric].agg(["count", "mean", "std"]).reset_index()
        g = g[g["count"] >= 20]
        if len(g) < 2:
            continue
        spread = float(g["mean"].max() - g["mean"].min())
        candidates.append(
            {
                "candidate_axis": name,
                "feature": col,
                "metric": metric,
                "n_levels_ge20": int(len(g)),
                "mean_spread": spread,
                "best_level": str(g.sort_values("mean", ascending=False).iloc[0][col]),
                "worst_level": str(g.sort_values("mean", ascending=True).iloc[0][col]),
                "status": "outcome_informed_discovery_only",
                "level_summary": g.sort_values("mean").to_dict(orient="records"),
            }
        )
    return sorted(candidates, key=lambda x: x["mean_spread"], reverse=True)


def write_claim_ledger():
    claims = [
        {
            "id": "C1_context_generalization",
            "source": "State manuscript abstract/results and README",
            "claim": "STATE predicts perturbation effects across diverse contexts and improves context generalization on chemical, signaling, and genetic perturbation datasets.",
            "scientific_unit": "perturbation-by-cell-context response example",
            "paper_protocol": "few-shot context generalization: target contexts contribute part of perturbations to training; remaining perturbations are held out in that context",
            "spectra_risk": "The same perturbation may be present in other training contexts, so this is not global perturbation novelty.",
        },
        {
            "id": "C2_embedding_transfer",
            "source": "State manuscript results and README",
            "claim": "SE-trained representations enable transfer across datasets and improve novel-context performance with less data.",
            "scientific_unit": "dataset/context-level perturbation response examples",
            "paper_protocol": "ST+SE compared with ST+HVG and other baselines on public/preprint splits",
            "spectra_risk": "Precomputed model-card results are author-produced; independent target rerun needs checkpoints plus H5ADs.",
        },
        {
            "id": "C3_novel_context_no_perturbations",
            "source": "State manuscript abstract and zero-shot TOMLs",
            "claim": "STATE can identify strong perturbations in novel cellular contexts where no perturbations were observed during training.",
            "scientific_unit": "perturbation-by-heldout-cell-context response example",
            "paper_protocol": "zeroshot context holdout",
            "spectra_risk": "Only five Tahoe zero-shot contexts in scored artifacts; context-similarity axis is underpowered without downloading/running more data.",
        },
    ]
    (ART / "hypothesis_ledger.json").write_text(json.dumps(claims, indent=2))


def main():
    ART.mkdir(exist_ok=True)
    SPECTRA.mkdir(exist_ok=True)
    manifest = get_hf_file_manifest()
    write_claim_ledger()

    all_df, download_log = load_target_results(manifest)
    all_df["row_key"] = np.arange(len(all_df)).astype(str)
    drug_meta, gene_meta, cell_meta = load_tahoe_metadata()
    all_df = attach_drug_metadata(all_df, drug_meta)
    all_df = compute_context_chemical_axis(all_df, drug_meta)
    all_df.to_csv(ROOT / "target_model_results.csv", index=False)

    tahoe_chem = all_df[
        (all_df["dataset_family"] == "Tahoe-100M")
        & (all_df["protocol"] == "fewshot")
        & all_df["chem_support_level"].notna()
    ].copy()
    tahoe_chem.to_csv(SPECTRA / "tahoe_fewshot_chemical_support_examples.csv", index=False)

    spc_frames = []
    trend_records = []
    for rep in sorted(tahoe_chem["representation"].dropna().unique()):
        sub = tahoe_chem[tahoe_chem["representation"] == rep]
        summ = summarize_axis(
            sub,
            "chem_support_level",
            "max_tanimoto_to_target_context_train_drug",
            f"Tahoe fewshot target-context chemical support {rep}",
        )
        summ["representation"] = rep
        spc_frames.append(summ)
        for metric in ["overlap_at_N", "de_sig_genes_recall", "de_spearman_lfc_sig", "pearson_delta", "mse_delta"]:
            tr = metric_trend(summ, metric)
            tr["representation"] = rep
            trend_records.append(tr)
    spc = pd.concat(spc_frames, ignore_index=True)
    spc.to_csv(ART / "spc_tahoe_fewshot_target_context_chemical_support.csv", index=False)
    pd.DataFrame(trend_records).to_csv(ART / "spc_tahoe_fewshot_target_context_chemical_support_trends.csv", index=False)

    # Dose is a prospectively definable protocol axis, but it is not a train-test similarity axis
    # because all dose levels are represented in training via other perturbations.
    dose = dose_axis(all_df)
    dose_summaries = []
    for rep in sorted(dose["representation"].dropna().unique()):
        sub = dose[dose["representation"] == rep].copy()
        if sub["dose_level"].nunique() >= 3:
            # Treat numeric dose as an ordered protocol feature, not decreasing train-test similarity.
            sub["dose_level"] = pd.Categorical(sub["dose_level"], ordered=True)
            summ = summarize_axis(sub, "dose_level", "dose", f"Tahoe fewshot dose protocol {rep}")
            summ["representation"] = rep
            dose_summaries.append(summ)
    if dose_summaries:
        pd.concat(dose_summaries, ignore_index=True).to_csv(ART / "exploratory_tahoe_dose_protocol_curve.csv", index=False)

    discovery = all_scored_axis_discovery(all_df)
    (ART / "all_scored_axis_discovery.json").write_text(json.dumps(discovery, indent=2, default=str))

    # Axis ledger and audit status.
    sim_progression = spc.groupby("representation").apply(
        lambda x: x.sort_values("similarity_mean", ascending=False)["similarity_mean"].tolist(),
        include_groups=False,
    )
    decreasing_ok = all(
        all(a >= b for a, b in zip(vals, vals[1:]))
        for vals in sim_progression.tolist()
    )
    trend_df = pd.DataFrame(trend_records)
    chem_status = "valid_negative_or_weak"  # updated below if large consistent degradation is present
    degradation_hits = trend_df[
        (trend_df["metric"].isin(["overlap_at_N", "de_sig_genes_recall", "pearson_delta"]))
        & (trend_df["relative_far_minus_near"] < -0.10)
        & (trend_df["pearson_level_corr_with_similarity"] > 0.5)
    ]
    if len(degradation_hits) >= 2:
        chem_status = "promising_degradation_needs_independent_confirmation"

    axis_ledger = [
        {
            "axis_id": "A1_tahoe_target_context_chemical_support",
            "status": chem_status,
            "frozen_before_full_target_scoring": True,
            "schema_probe_exposure": "One C32 ST-HVG result CSV was opened before this script for column inspection only; confirmation summaries use the full loaded Tahoe pool and are not selected by target error.",
            "unit": "Tahoe perturbation-by-cell-context-by-dose examples, analyzed separately for ST-HVG and ST-SE",
            "axis_definition": "For each held-out Tahoe few-shot target-context drug/dose, compute RDKit Morgan Tanimoto similarity to the nearest drug that is observed in that same target context's training subset. Split into five equal-frequency levels using the similarity feature only.",
            "direction": "L1_near has highest target-context training support; L5_far has lowest support.",
            "validity_checks": {
                "nontrivial_levels": int(spc["level"].nunique()),
                "min_rows_per_level_per_representation": int(spc["n_rows"].min()),
                "similarity_decreases_when_ordered": bool(decreasing_ok),
                "label_or_target_error_used_for_membership": False,
                "target_model_confidence_used_for_membership": False,
                "fixed_baseline": "Zero-response baseline for DE overlap/recall and DE-count MAE; stronger context/perturb-mean baselines require raw train labels or author baseline artifacts not present in small scored CSVs.",
                "mapping_rate_exact_or_loose": float((tahoe_chem["drug_metadata_match"] != "missing").mean()),
            },
            "claim_boundary": "Valid only for target-context chemical support in the official Tahoe few-shot context-generalization setup. It is not global unseen-drug generalization because the same drugs may appear in other training contexts.",
            "primary_artifacts": [
                "spectra_ready_dataset/tahoe_fewshot_chemical_support_examples.csv",
                "artifacts/spc_tahoe_fewshot_target_context_chemical_support.csv",
                "artifacts/spc_tahoe_fewshot_target_context_chemical_support_trends.csv",
            ],
        },
        {
            "axis_id": "A2_tahoe_dose_protocol",
            "status": "exploratory_invalid_as_spc_similarity",
            "axis_definition": "Dose level of held-out Tahoe perturbation (0.05, 0.5, 5.0 uM).",
            "reason": "Dose is prospective, but it is not a decreasing train-test similarity axis in the official splits because all dose levels are represented in training through other perturbations.",
            "primary_artifacts": ["artifacts/exploratory_tahoe_dose_protocol_curve.csv"],
        },
        {
            "axis_id": "A3_all_scored_axis_discovery",
            "status": "outcome_informed_discovery_only",
            "axis_definition": "Prospective metadata features mined after scored evidence: dataset family, representation, Tahoe MOA fields, dose.",
            "reason": "These hypotheses require a frozen confirmation panel before any paper-facing claim.",
            "primary_artifacts": ["artifacts/all_scored_axis_discovery.json"],
        },
    ]
    (ROOT / "axis_ledger.json").write_text(json.dumps(axis_ledger, indent=2, default=str))

    commands = [
        {"command": "clone ArcInstitute/state, cell-eval, cell-load", "purpose": "official source inspection"},
        {"command": "download OpenReview STATE PDF and pdftotext", "purpose": "claim extraction"},
        {"command": "HuggingFace API model/dataset manifest", "purpose": "access and feasibility audit"},
        {"command": "download only *_results.csv plus small Tahoe metadata parquet files", "purpose": "bounded target-score and prospective-feature table construction"},
        {"command": "scripts/run_state_spectra_audit.py", "purpose": "single-controller SPECTRA table, axis, SPC, and ledger generation"},
    ]
    (ROOT / "commands_run.json").write_text(json.dumps(commands, indent=2))

    state = {
        "updated_utc": now_iso(),
        "status": "analysis_complete_needs_terminal_decision",
        "source_repos": {
            "state_commit": os.popen(f"git -C {STATE} rev-parse HEAD").read().strip(),
            "hf_manifest": "artifacts/hf_resource_manifest.json",
        },
        "target_results_rows": int(len(all_df)),
        "target_results_by_dataset_protocol_representation": all_df.groupby(
            ["dataset_family", "protocol", "representation"], dropna=False
        ).size().reset_index(name="rows").to_dict(orient="records"),
        "primary_axis_status": chem_status,
        "primary_axis_validity": axis_ledger[0]["validity_checks"],
        "hard_blockers": [],
        "nonterminal_followups": discovery[:3],
    }
    (ROOT / "spectra_loop_state.json").write_text(json.dumps(state, indent=2, default=str))

    print(json.dumps({
        "target_results_rows": len(all_df),
        "tahoe_chem_rows": len(tahoe_chem),
        "spc_path": str(ART / "spc_tahoe_fewshot_target_context_chemical_support.csv"),
        "trend_path": str(ART / "spc_tahoe_fewshot_target_context_chemical_support_trends.csv"),
        "chem_status": chem_status,
        "discovery_top": discovery[:2],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
