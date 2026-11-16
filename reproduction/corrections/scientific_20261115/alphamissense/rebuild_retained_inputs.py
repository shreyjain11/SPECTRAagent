from pathlib import Path
import json,tarfile,gzip,io,re,hashlib,sys,tempfile
from collections import defaultdict
import numpy as np,pandas as pd
from Bio.Align import substitution_matrices
from scipy.stats import spearmanr
R=Path(__file__).resolve().parents[3]
B=R/'primary/alphamissense/payloads'
O=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='am-primary-retained-'));O.mkdir(parents=True,exist_ok=True)
t=tarfile.open(B/'am-frozen-panel-and-score-inputs.tar.gz')
meta=pd.read_csv(t.extractfile('am-primary/inputs/proteingym/kept_assays_verified.tsv'),sep='\t')
scores=defaultdict(dict);wt=defaultdict(dict)
with gzip.open(t.extractfile('am-primary/inputs/official_scores_64_proteins.tsv.gz'),'rt') as f:
 for line in f:
  p=line.rstrip().split('\t');m=re.fullmatch(r'([A-Z])(\d+)([A-Z])',p[1])
  if m:scores[p[0]][int(m[2]),m[3]]=float(p[2]);wt[p[0]][int(m[2])]=m[1]
t.close()
A={}
with tarfile.open(B/'am-recorded-alignment-results.tar.gz') as t:
 for n in t.getnames():
  if n.endswith('.npz'):
   z=np.load(io.BytesIO(t.extractfile(n).read()),allow_pickle=False)
   A[Path(n).name.removesuffix('.npz')]={k:z[k] for k in z.files}
blosum=substitution_matrices.load('BLOSUM62');AA_INDEX={a:i for i,a in enumerate('ACDEFGHIKLMNPQRSTVWY')}
rows=[];coverage=[];position=[]
with tarfile.open(B/'am-original-dms-members.tar.gz') as t:
 for m in meta.to_dict('records'):
  aid=m['DMS_id'];acc=m['resolved_accession'];data=pd.read_csv(t.extractfile('am-primary/inputs/proteingym/dms_final_73/'+m['DMS_filename']))
  wild=wt[acc];seq=''.join(wild.get(i,'X') for i in range(1,max(wild)+1));offset=seq.find(m['target_seq'])
  a=A[m['MSA_filename']];cols={int(p):i for i,p in enumerate(a['positions'])};inserts=set(a['lowcov'].astype(int));eligible=scored=0
  for d in data.itertuples():
   match=re.fullmatch(r'([ACDEFGHIKLMNPQRSTVWY])(\d+)([ACDEFGHIKLMNPQRSTVWY])',str(d.mutant))
   if not match:continue
   w,p,alt=match[1],int(match[2]),match[3]
   if not 1<=p<=len(m['target_seq']) or m['target_seq'][p-1]!=w:continue
   if p in cols:
    col=cols[p];occ=round(float(a['occupancy'][col]),4);neff=round(float(a['neff'][col]),3);ins=False
   elif p in inserts:col=None;occ=neff=np.nan;ins=True
   else:continue
   eligible+=1;position.append(dict(assay=aid,position=p,occupancy=occ,neff=neff,insertion=ins,column=col));cp=offset+p
   if offset<0 or wild.get(cp)!=w:continue
   am=scores[acc].get((cp,alt))
   if am is None:continue
   pssm=np.nan
   if not ins:
    c=a['counts'][col];pssm=float(np.log((c[AA_INDEX[alt]]+.5)/(c[AA_INDEX[w]]+.5)))
   rows.append(dict(assay=aid,accession=acc,msa=m['MSA_filename'],position=p,wt=w,alt=alt,mutant=d.mutant,fitness=float(d.DMS_score),family='Tsuboyama domains' if 'Tsuboyama' in aid else 'Other assays',msa_start=int(m['MSA_start']),msa_end=int(m['MSA_end']),occupancy=occ,neff=neff,insertion=ins,column=col,terminal=(p-int(m['MSA_start'])<20 or int(m['MSA_end'])-p<20),am=am,blosum=float(blosum[w,alt]),pssm=pssm));scored+=1
  coverage.append(dict(assay=aid,accession=acc,eligible_variants=eligible,scored_variants=scored,sequence_offset=offset))
panel=pd.DataFrame(rows);panel.to_pickle(O/'candidate_panel.pkl');pd.DataFrame(coverage).to_csv(O/'candidate_coverage.csv',index=False)
pd.DataFrame(position).drop_duplicates(['assay','position']).to_csv(O/'candidate_position_features.csv',index=False)
print('panel',len(panel),panel.assay.nunique(),panel.accession.nunique(),flush=True)
# Reuse unchanged feature selection and per-assay calculation from each baseline notebook.
for axis in range(3,8):
 n=json.load(open(R/f'inline/alphamissense/am-primary/axis-{axis}.ipynb'))
 source=next(''.join(c['source']) for c in n['cells'] if c['cell_type']=='code' and 'AXIS_NUMBER=' in ''.join(c['source']))
 first=source.split("for (level,score),d in per_assay.groupby")[0]
 scope=dict(panel=panel,np=np,pd=pd,spearmanr=spearmanr);exec(first,scope)
 q=scope['per_assay'];q.to_csv(O/f'axis-{axis}-per_assay.csv',index=False)
 curves=q.groupby(['level','score']).apply(lambda g:pd.Series({'weighted_abs_rho':np.average(g.abs_rho,weights=g.n),'assays':len(g),'proteins':g.protein.nunique(),'variants':g.n.sum()}),include_groups=False).reset_index()
 print('axis',axis,curves[curves.score=='am'].to_string(index=False),flush=True)
 for name in ['signal','composition']:
  scope[name].to_csv(O/f'axis-{axis}-{name}.csv',index=False)
