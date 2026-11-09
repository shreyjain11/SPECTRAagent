#!/usr/bin/env python3
"""Extract two REAL alignment-column windows (one gappy/low-occupancy, one clean/conserved) from a
real ProteinGym a2m, for the figure's cartoons. Columns chosen to match the FROZEN occupancy values;
rows evenly sampled across the MSA so the displayed column reflects its true occupancy. New file."""
import zipfile, os, csv, json
import numpy as np
OUT="/home/shreyjain/spectra_alphamissense/stepB"; PG="/home/shreyjain/spectra_alphamissense/proteingym"
mzip=zipfile.ZipFile(f"{OUT}/DMS_msa_files_v1.3.zip"); mnames={os.path.basename(n):n for n in mzip.namelist()}
RM_INS=str.maketrans("","","abcdefghijklmnopqrstuvwxyz.")

# assay meta
meta={}
with open(f"{PG}/kept_assays_verified.tsv") as fh:
    for r in csv.DictReader(fh,delimiter="\t"):
        meta[r["DMS_id"]]={"mfn":r["MSA_filename"].strip(),
                           "start":int(float(r["MSA_start"])) if r["MSA_start"] else None}
# frozen occupancy per (assay,pos)
occ=lambda:0
focc={}
with open(f"{OUT}/axis3_pathC_percolumn_FROZEN.tsv") as fh:
    for r in csv.DictReader(fh,delimiter="\t"):
        if r["low_cov_insert"]=="1" or not r["occupancy"].strip(): continue
        focc.setdefault(r["assay"],{})[int(r["target_pos"])]=float(r["occupancy"])

PREF=["MSH2_HUMAN_Jia_2020","NPC1_HUMAN_Erwood_2022_RPE1","CBS_HUMAN_Sun_2020",
      "VKOR1_HUMAN_Chiasson_2020_activity","MTHR_HUMAN_Weile_2021","PTEN_HUMAN_Mighell_2018",
      "CCR5_HUMAN_Gill_2023","SC6A4_HUMAN_Young_2021"]
cands=[a for a in PREF if a in meta and a in focc]+[a for a in focc if a not in PREF]

def build(assay):
    mfn=meta[assay]["mfn"]; start=meta[assay]["start"]
    # focus row0 -> pos2mc
    focus=None
    with mzip.open(mnames[mfn]) as fh:
        cur=[]
        for rawl in fh:
            line=rawl.decode("latin1").rstrip("\n")
            if line.startswith(">"):
                if focus is None and cur: focus="".join(cur); break
                cur=[]
            else: cur.append(line)
        if focus is None and cur: focus="".join(cur)
    pos2mc={}; mc=0
    for i,c in enumerate(focus):
        tp=start+i
        if not (c.islower() or c=="."): pos2mc[tp]=mc; mc+=1
    ncol=mc
    # choose target positions from frozen occupancy
    items=[(p,o) for p,o in focc[assay].items() if p in pos2mc]
    if not items: return None
    gappy=min(items,key=lambda x:abs(x[1]-0.25))     # ~0.25 occupancy
    cleans=[(p,o) for p,o in items if o>=0.999]
    if gappy[1]>0.5 or not cleans: return None
    mid=start+len(focus)//2
    clean=min(cleans,key=lambda x:abs(x[0]-mid))
    gmc=pos2mc[gappy[0]]; cmc=pos2mc[clean[0]]
    # collect window match-col chars for ALL rows (7 cols around each focal)
    def win(mcidx): return (max(0,mcidx-3),min(ncol,mcidx+4))
    gw=win(gmc); cw=win(cmc)
    grows=[]; crows=[]
    rid=0; cur=[]
    def flush():
        if not cur: return
        s="".join(cur).translate(RM_INS)
        s=s+"-"*(ncol-len(s)) if len(s)<ncol else s[:ncol]
        grows.append(s[gw[0]:gw[1]]); crows.append(s[cw[0]:cw[1]])
    with mzip.open(mnames[mfn]) as fh:
        for rawl in fh:
            line=rawl.decode("latin1").rstrip("\n")
            if line.startswith(">"): flush(); cur=[]
            else: cur.append(line)
        flush()
    n=len(grows)
    idx=[int(round(x)) for x in np.linspace(0,n-1,12)]
    gsel=[grows[i] for i in idx]; csel=[crows[i] for i in idx]
    return {"assay":assay,"gene":assay.split("_")[0],
            "gappy":{"rows":gsel,"focal":gmc-gw[0],"occ":round(gappy[1],3),"pos":gappy[0]},
            "clean":{"rows":csel,"focal":cmc-cw[0],"occ":round(clean[1],3),"pos":clean[0]},
            "nseq":n}

out=None
for a in cands:
    try:
        r=build(a)
    except Exception as e:
        r=None
    if r:
        # require the gappy window focal col to actually show some gaps among sampled rows
        col=[row[r["gappy"]["focal"]] if len(row)>r["gappy"]["focal"] else "-" for row in r["gappy"]["rows"]]
        ngap=sum(1 for c in col if c=="-")
        if ngap>=4:
            out=r; break
if out is None:
    raise SystemExit("no suitable assay found")
json.dump(out,open(f"{OUT}/cartoon_columns.json","w"),indent=1)
print(f"chosen assay: {out['assay']}  nseq={out['nseq']}")
print(f"gappy pos={out['gappy']['pos']} occ={out['gappy']['occ']} focal_idx={out['gappy']['focal']}")
for row in out["gappy"]["rows"]: print("  ",row)
print(f"clean pos={out['clean']['pos']} occ={out['clean']['occ']} focal_idx={out['clean']['focal']}")
for row in out["clean"]["rows"]: print("  ",row)
print("WROTE cartoon_columns.json")
