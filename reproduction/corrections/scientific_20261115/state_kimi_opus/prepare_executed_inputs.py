from pathlib import Path
import json,hashlib,shutil,pandas as pd,numpy as np
R=Path('/private/tmp/spectra-pr-review-20261115');E=R/'reproduction/corrections/scientific_20261115/state_kimi_opus';T=Path('/private/tmp/state-scientific-correction-20261115');A=Path('/Users/shreyjain/Documents/Codex/2026-10-22/do-you-have-the-extra-state/outputs/NOV6_REPRODUCIBILITY/state/assets');inventory=json.load(open(A.parent/'STATE_INPUTS.json'));evidence=[]
def copy_input(key):
 p=A/key;j=inventory[key];sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha==j['sha256'] and p.stat().st_size==j['bytes'],key
 q=T/'work'/key;q.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,q)
 evidence.append({'public_archive':'https://github.com/shreyjain11/SPECTRAagent/releases/download/notebook-inputs-2026-11-08-v1/state-inputs.zip','archive_member':'assets/'+key,'bytes':p.stat().st_size,'sha256':sha,'local_staged_input':str(q)})
 return q
for c in ['rpe1','jurkat','hepg2']:
 copy_input(f'state-kimi-r1/results/per_unit_scores_{c}.csv');copy_input(f'state-kimi-r1/results/proximity_embedding_norms_{c}.csv')
for name in ['per_unit_scores.csv','analysis_summary.json']:
 copy_input('state-kimi-r1/results/'+name)
for name in ['data/predictions.csv','spectra_run/artifacts/replogle_go_features.csv','spectra_run/artifacts/go_terms.json']:
 copy_input('state-opus-r2/'+name)
# Verify every retained zero-shot Replogle metric against current pinned public source bytes.
sources=json.load(open('/private/tmp/state-opus-official-sources.json'));p=T/'work/state-opus-r2/data/predictions.csv';d=pd.read_csv(p,low_memory=False);maxdiff=0.0;checked=0
for x in sources:
 f=T/'official'/x['path'];assert hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'];s=pd.read_csv(f);q=d[(d.source_repo==x['repo'])&(d.source_path==x['filename'])];m=q.merge(s,on='perturbation',validate='one_to_one',suffixes=('_retained','_official'));assert len(m)==len(q)==len(s)
 for col in s.select_dtypes('number').columns:
  if col in q.columns:
   a=m[col+'_retained'].to_numpy();b=m[col+'_official'].to_numpy();assert np.array_equal(np.isnan(a),np.isnan(b));diff=np.nanmax(np.abs(a-b)) if np.isfinite(a).any() else 0.0;assert diff<1e-12,(col,diff);maxdiff=max(maxdiff,float(diff));checked+=1
 evidence.append({'url':x['url'],'bytes':x['bytes'],'sha256':x['sha256'],'role':'pinned official source verification of retained zero-shot scores','local_staged_input':str(f)})
# Recompute the feature from its annotation source, using exact original cell7.
nb=json.load(open(R/'reproduction/inline/state/state-opus-r2/test-05.ipynb'));namespace={'P':T/'work/state-opus-r2','WORK':T/'work/state-opus-r2'};old=pd.read_csv(T/'work/state-opus-r2/spectra_run/artifacts/replogle_go_features.csv');exec(''.join(nb['cells'][7]['source']),namespace);new=pd.read_csv(T/'work/state-opus-r2/spectra_run/artifacts/replogle_go_features.csv');pd.testing.assert_frame_equal(old[new.columns],new,check_exact=False,rtol=1e-12,atol=1e-12)
(E/'input_evidence.json').write_text(json.dumps({'inputs':evidence,'official_verification':{'source_files':len(sources),'metric_column_comparisons':checked,'max_absolute_difference':maxdiff},'feature_reconstruction':'Recomputed original GO-BP top5 Jaccard feature from go_terms.json; all five recomputed columns identical to retained feature table within1e-12; retained table also has three extra unused annotation fields.','no_model_inference':True},indent=2)+'\n');print('verified',len(evidence),'inputs;official score maxdifference',maxdiff)
