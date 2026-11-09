#!/usr/bin/env python3
"""Step A prep: map ProteinGym UniProt entry-names -> accessions, emit candidate
accession set for the AM scan, and report human-mapping coverage.

Read-only except for writing work/cand_acc.txt and work/step_a_assay_candidates.tsv.
Does NOT scan the 1.2GB AM file (that is the next, awk stage).
"""
import gzip, csv, os
import pandas as pd

ROOT = "/home/shreyjain/spectra_alphamissense"
DATA = f"{ROOT}/data"
WORK = f"{ROOT}/work"
PG   = f"{ROOT}/proteingym/DMS_substitutions.csv"

# ---- 1. entry-name -> accession map from UniProt human FASTAs (canonical first) ----
entry2acc = {}
def load_fasta_map(path):
    n = 0
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if not line.startswith(">"):
                continue
            parts = line[1:].split("|")
            if len(parts) < 3:
                continue
            acc = parts[1]
            entryname = parts[2].split()[0]
            if entryname not in entry2acc:          # canonical/first wins
                entry2acc[entryname] = acc
                n += 1
    return n

n_can = load_fasta_map(f"{DATA}/human_canonical.fasta.gz")
n_add = load_fasta_map(f"{DATA}/human_additional.fasta.gz")
print(f"entry2acc: {n_can} from canonical (+{n_add} new from additional) = {len(entry2acc)}")

# ---- 2. ProteinGym metadata -> candidate accessions per assay ----
df = pd.read_csv(PG)
print(f"PG assays: {len(df)}")

def candidates(entry):
    cands = []
    a1 = entry2acc.get(entry)              # fasta-mapped accession
    if a1:
        cands.append(a1)
    a2 = str(entry).split("_")[0]          # prefix fallback (works for TrEMBL acc_ORG ids)
    if a2 and a2 not in cands:
        cands.append(a2)
    return cands, (a1 is not None)

rows, all_cands = [], set()
for _, r in df.iterrows():
    entry = r["UniProt_ID"]
    cands, mapped = candidates(entry)
    all_cands.update(cands)
    rows.append({
        "DMS_id": r["DMS_id"],
        "entry_name": entry,
        "taxon": r["taxon"],
        "fasta_mapped": int(mapped),
        "candidates": "|".join(cands),
        "seq_len": int(r["seq_len"]),
        "n_single": int(r["DMS_number_single_mutants"]),
        "n_total": int(r["DMS_total_number_mutants"]),
    })

os.makedirs(WORK, exist_ok=True)
with open(f"{WORK}/step_a_assay_candidates.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
    w.writeheader(); w.writerows(rows)

with open(f"{WORK}/cand_acc.txt", "w") as fh:
    for a in sorted(all_cands):
        fh.write(a + "\n")
print(f"unique candidate accessions written: {len(all_cands)} -> work/cand_acc.txt")

# ---- 3. human-mapping coverage diagnostics ----
hum = df[df["taxon"].astype(str).str.contains("Human", case=False, na=False)]
mapped = [e for e in hum["UniProt_ID"] if e in entry2acc]
unmapped = [e for e in hum["UniProt_ID"] if e not in entry2acc]
print(f"\nHUMAN assays: {len(hum)}  | entry-name mapped via FASTA: {len(mapped)}  | unmapped: {len(unmapped)}")
if unmapped:
    print("  unmapped human entry-names (will rely on prefix fallback):")
    for e in sorted(set(unmapped)):
        print(f"    {e}  -> prefix '{str(e).split('_')[0]}'")
