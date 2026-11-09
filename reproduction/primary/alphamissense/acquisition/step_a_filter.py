#!/usr/bin/env python3
"""SPECTRA AlphaMissense audit -- STEP A only.

Prospective inclusion filter for the ProteinGym substitution benchmark:
  KEEP an assay iff
    (1) its UniProt accession is in AM's released substitution set, AND
    (2) its ProteinGym reference sequence matches AM's canonical UniProt
        sequence at >= 99% identity over the FULL global-aligned length
        (Needleman-Wunsch, no terminal trim).

"AM's canonical sequence" is reconstructed directly from the AM substitution
file (the WT residue of every protein_variant), i.e. exactly what AM scored.

NO target-model scores/confidence are read. NO measurements are downloaded.
Outputs kept + dropped lists with reasons; flags if < ~15-20 survive.
"""
import gzip, csv, json, re, os
import pandas as pd
from Bio import Align
import Bio

ROOT = "/home/shreyjain/spectra_alphamissense"
DATA = f"{ROOT}/data"
WORK = f"{ROOT}/work"
ART  = f"{ROOT}/artifacts"
PG   = f"{ROOT}/proteingym/DMS_substitutions.csv"
AM_FILE = f"{DATA}/AlphaMissense_aa_substitutions.tsv.gz"
ID_THRESHOLD = 99.0

VAR_RE = re.compile(r"^([A-Z])(\d+)([A-Z])$")

# ---- 1. Reconstruct AM canonical sequences from candidate substitution rows ----
print("[1] reconstructing AM canonical sequences from WT residues ...", flush=True)
am_wt = {}   # acc -> {pos: wt_aa}
with open(f"{WORK}/am_candidate_subs.tsv") as fh:
    for line in fh:
        acc, var = line.rstrip("\n").split("\t")
        m = VAR_RE.match(var)
        if not m:
            continue
        wt, pos = m.group(1), int(m.group(2))
        d = am_wt.setdefault(acc, {})
        if pos not in d:
            d[pos] = wt

am_seq, am_gaps = {}, {}
for acc, d in am_wt.items():
    L = max(d)
    seq = "".join(d.get(i, "X") for i in range(1, L + 1))
    am_seq[acc] = seq
    am_gaps[acc] = seq.count("X")
print(f"    reconstructed {len(am_seq)} AM accessions; "
      f"{sum(1 for g in am_gaps.values() if g)} have internal gaps", flush=True)

# ---- 2. Load assay candidates + target_seq ----
cand = pd.read_csv(f"{WORK}/step_a_assay_candidates.tsv", sep="\t")
pg = pd.read_csv(PG)[["DMS_id", "target_seq"]]
df = cand.merge(pg, on="DMS_id", how="left")
print(f"[2] assays: {len(df)}", flush=True)

# ---- 3. Global aligner (NW, end-gap penalised => no terminal trim) ----
aligner = Align.PairwiseAligner()
aligner.mode = "global"
aligner.match_score = 1.0
aligner.mismatch_score = -1.0
aligner.open_gap_score = -2.0
aligner.extend_gap_score = -0.5

def global_identity(a, b):
    """% identity over full aligned length (incl terminal gap columns)."""
    aln = aligner.align(a, b)[0]
    row_a, row_b = aln[0], aln[1]
    n = len(row_a)
    ident = sum(1 for x, y in zip(row_a, row_b) if x == y and x != "-")
    return 100.0 * ident / n, n, ident

# ---- 4. Apply filter ----
print(f"[4] filtering (membership + >= {ID_THRESHOLD}% global identity) ...", flush=True)
kept, dropped = [], []
for _, r in df.iterrows():
    cands = str(r["candidates"]).split("|")
    chosen = next((c for c in cands if c in am_seq), None)
    if chosen is None:
        dropped.append({
            "DMS_id": r["DMS_id"], "entry_name": r["entry_name"], "taxon": r["taxon"],
            "candidate_acc": cands[0] if cands else "", "am_accession": "",
            "reason": "uniprot_not_in_AM", "identity_pct": "",
            "pg_seq_len": r["seq_len"], "am_seq_len": "",
            "n_single": r["n_single"], "n_total": r["n_total"],
        })
        continue
    pg_seq = str(r["target_seq"]).strip().upper().replace("*", "")
    am = am_seq[chosen]
    pct, alen, ident = global_identity(am, pg_seq)
    rec = {
        "DMS_id": r["DMS_id"], "entry_name": r["entry_name"], "taxon": r["taxon"],
        "am_accession": chosen, "identity_pct": round(pct, 3),
        "pg_seq_len": int(r["seq_len"]), "am_seq_len": len(am),
        "aligned_len": alen, "n_single": int(r["n_single"]), "n_total": int(r["n_total"]),
    }
    if pct >= ID_THRESHOLD:
        kept.append(rec)
    else:
        rec["reason"] = "identity_below_99"
        rec["candidate_acc"] = chosen
        dropped.append(rec)

kept.sort(key=lambda x: (-x["identity_pct"], x["DMS_id"]))
dropped.sort(key=lambda x: (x["reason"], x["entry_name"]))

# ---- 5. Write artifacts ----
os.makedirs(ART, exist_ok=True)
kept_cols = ["DMS_id", "entry_name", "am_accession", "identity_pct",
             "n_single", "n_total", "pg_seq_len", "am_seq_len", "aligned_len"]
with open(f"{ART}/step_a_kept_assays.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=kept_cols, extrasaction="ignore"); w.writeheader(); w.writerows(kept)
drop_cols = ["DMS_id", "entry_name", "taxon", "candidate_acc", "am_accession",
             "reason", "identity_pct", "pg_seq_len", "am_seq_len", "n_single", "n_total"]
with open(f"{ART}/step_a_dropped_assays.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=drop_cols, extrasaction="ignore"); w.writeheader(); w.writerows(dropped)

from collections import Counter
drop_reasons = Counter(d["reason"] for d in dropped)
n_uniq_prot = len({k["am_accession"] for k in kept})
report = {
    "step": "A",
    "description": "Human-only (AM-membership) + isoform (>=99% global identity, no terminal trim) filter on ProteinGym substitutions",
    "n_assays_total": len(df),
    "n_kept": len(kept),
    "n_dropped": len(dropped),
    "n_kept_unique_proteins": n_uniq_prot,
    "drop_reasons": dict(drop_reasons),
    "kept_identity_min": round(min((k["identity_pct"] for k in kept), default=0.0), 3),
    "kept_single_mutants_total": sum(k["n_single"] for k in kept),
    "stability_flag": ("OK" if len(kept) >= 20 else
                       ("MARGINAL_15_20" if len(kept) >= 15 else "LOW_BELOW_15")),
    "identity_threshold_pct": ID_THRESHOLD,
    "provenance": {
        "am_substitutions_file": AM_FILE,
        "am_canonical_sequence_source": "reconstructed from WT residue of AM protein_variant (acc in AM set)",
        "proteingym_metadata": PG,
        "accession_map_source": ["data/human_canonical.fasta.gz", "data/human_additional.fasta.gz"],
        "alignment": f"Biopython {Bio.__version__} PairwiseAligner global; "
                     f"match=1,mismatch=-1,open=-2,extend=-0.5; identity=identical_cols/full_aligned_len",
        "variant_counts_from": "ProteinGym metadata (DMS_number_single_mutants / DMS_total_number_mutants); no measurements downloaded",
        "am_internal_seq_gaps": {a: g for a, g in am_gaps.items() if g},
    },
}
with open(f"{ART}/step_a_report.json", "w") as fh:
    json.dump(report, fh, indent=2)

# ---- 6. Console summary ----
print("\n===================== STEP A SUMMARY =====================")
print(f"assays total: {report['n_assays_total']}   KEPT: {report['n_kept']}   DROPPED: {report['n_dropped']}")
print(f"kept unique proteins: {n_uniq_prot}   kept min identity: {report['kept_identity_min']}%")
print(f"drop reasons: {dict(drop_reasons)}")
print(f"stability flag: {report['stability_flag']}  (need ~15-20 for bin stability)")
print("\n--- KEPT ASSAYS ---")
print(f"{'DMS_id':<46}{'acc':<11}{'id%':>7}{'n_single':>10}{'pg_len':>8}{'am_len':>8}")
for k in kept:
    print(f"{k['DMS_id']:<46}{k['am_accession']:<11}{k['identity_pct']:>7}{k['n_single']:>10}{k['pg_seq_len']:>8}{k['am_seq_len']:>8}")
print(f"\nartifacts: {ART}/step_a_kept_assays.csv, step_a_dropped_assays.csv, step_a_report.json")
