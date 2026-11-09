#!/usr/bin/env python3
"""Extract protein sequences for benchmark UniProt IDs -> query.fasta"""
import gzip, csv

DATA = "/home/shreyjain/spectra_alphamissense/data"
WORK = "/home/shreyjain/spectra_alphamissense/work"

# benchmark uniprot ids
need = set()
with open(f"{WORK}/clinvar_am_benchmark.tsv") as fh:
    r = csv.DictReader(fh, delimiter="\t")
    for row in r:
        need.add(row["uniprot_id"])
print(f"benchmark proteins needed: {len(need)}")

seqs = {}
def load(path):
    acc, buf = None, []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if line.startswith(">"):
                if acc and acc in need and acc not in seqs:
                    seqs[acc] = "".join(buf)
                # header: >sp|ACC|NAME ...  or >tr|ACC|NAME
                parts = line[1:].split("|")
                acc = parts[1] if len(parts) >= 2 else parts[0].split()[0]
                buf = []
            else:
                buf.append(line.strip())
    if acc and acc in need and acc not in seqs:
        seqs[acc] = "".join(buf)

load(f"{DATA}/human_canonical.fasta.gz")
print(f"after canonical: {len(seqs)}")
load(f"{DATA}/human_additional.fasta.gz")
print(f"after additional: {len(seqs)}")

missing = need - set(seqs)
print(f"missing sequences: {len(missing)} (e.g. {list(missing)[:10]})")

outp = f"{WORK}/query.fasta"
with open(outp, "w") as fh:
    for acc, s in seqs.items():
        fh.write(f">{acc}\n{s}\n")
print(f"wrote {outp} with {len(seqs)} sequences")
