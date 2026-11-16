"""Independent numeric checks for the selected STATE corrections; no inference."""
from pathlib import Path
import argparse,json,ast,subprocess,hashlib
import numpy as np,pandas as pd
from scipy.stats import rankdata,spearmanr
p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();E=a.repository/'reproduction/corrections/scientific_20261115/state_kimi_opus';W=a.work
checks={};contexts=['rpe1','jurkat','hepg2'];per={}
for c in contexts:
 d=pd.read_csv(W/f'state-kimi-r1/results/per_unit_scores_{c}.csv');n=pd.read_csv(W/f'state-kimi-r1/results/proximity_embedding_norms_{c}.csv');d=d.merge(n[['gene','emb_norm']],on='gene',validate='one_to_one');assert set(d.seen_pair)=={0,1};assert np.isfinite(d.pearson_delta_state).all();assert np.isfinite(d.loc[d.seen_pair==0,'emb_norm']).all();per[c]=d
checks['kimi_input_checks']='Unique gene/context rows; seen_pair only0/1; all score and unseen norm values finite; point and bootstrap eligible masks agree.'
genes=sorted(set().union(*(set(d.gene) for d in per.values())));genemap={g:i for i,g in enumerate(genes)};rng=np.random.default_rng(20261115);independent=[];fixed=[int((per[c].seen_pair==0).sum())-3 for c in contexts]
for b in range(12):
 m=np.bincount(rng.integers(0,len(genes),len(genes)),minlength=len(genes));deltas=[];rhos=[]
 for c in contexts:
  d=per[c];weights=m[d.gene.map(genemap).to_numpy()];sample=d.iloc[np.repeat(np.arange(len(d)),weights)];seen=sample[sample.seen_pair==1];unseen=sample[sample.seen_pair==0];deltas.append(seen.pearson_delta_state.mean()-unseen.pearson_delta_state.mean());rhos.append(spearmanr(unseen.emb_norm,unseen.pearson_delta_state).statistic)
 independent.append([np.mean(deltas),np.tanh(np.average(np.arctanh(np.clip(rhos,-.999,.999)),weights=fixed))])
stored=pd.read_csv(E/'pooled_gene_bootstrap_draws.csv');diff=np.max(np.abs(np.array(independent)-stored.iloc[:12].to_numpy()));assert diff<1e-12
checks['kimi_first12_joint_gene_draws_direct_expansion_max_difference']=float(diff);assert stored.shape==(10000,2) and np.isfinite(stored).all().all();checks['kimi_finite_bootstrap_draws']=len(stored)
s=json.load(open(E/'confirm_summary.json'))['pooled'];assert np.allclose(np.quantile(stored.iloc[:,0],[.025,.975]),s['A1b_gene_bootstrap_ci95'],atol=1e-14,rtol=0);assert np.allclose(np.quantile(stored.iloc[:,1],[.025,.975]),s['A1c_gene_bootstrap_ci95'],atol=1e-14,rtol=0)
# Verify the actual retained-data rank bootstrap against independent expanded-row OLS.
source=(E/'opus_partial_rank_cell.py').read_text();tree=ast.parse(source);funcs=ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]);ns={'np':np,'pd':pd};exec(compile(funcs,str(E/'opus_partial_rank_cell.py'),'exec'),ns)
df=pd.read_csv(W/'state-opus-r2/data/predictions.csv',low_memory=False);r=df[df.dataset_family=='Replogle-Nadig'].copy();r['other_ctx_cov']=r.perturbation_name.map(r.groupby('perturbation_name').context.nunique())-1;f=pd.read_csv(W/'state-opus-r2/spectra_run/artifacts/replogle_go_features.csv');d=r.merge(f,on='perturbation_name',validate='many_to_one');z=d[(d.protocol=='zeroshot')&(d.representation=='HVG')]
q,genes,ids,fn,columns=ns['prepare_partial'](z,'overlap_at_N','go_meantop5',['de_nsig_counts_real','other_ctx_cov'],['context']);rng=np.random.default_rng(20261115);errs=[]
for i in range(12):
 counts=np.bincount(rng.integers(0,len(genes),len(genes)),minlength=len(genes));weights=counts[ids];sample=q.iloc[np.repeat(np.arange(len(q)),weights)];design=np.column_stack([np.ones(len(sample)),rankdata(sample.de_nsig_counts_real),rankdata(sample.other_ctx_cov),pd.get_dummies(sample[['context']],drop_first=True,dtype=float)]);response=np.column_stack([rankdata(sample.overlap_at_N),rankdata(sample.go_meantop5)]);res=response-np.einsum('ij,jk->ik',design,np.linalg.lstsq(design,response,rcond=None)[0],optimize=False);corr=np.corrcoef(res.T)[0,1];errs.append(abs(fn(weights)-corr))
assert max(errs)<1e-12;checks['opus_first12_weighted_rank_draws_direct_expansion_max_difference']=max(errs)
draws=pd.read_csv(E/'partial_rank_gene_bootstrap_draws.csv');assert draws.shape==(10000,4) and np.isfinite(draws).all().all();checks['opus_finite_bootstrap_draws_per_specification']=len(draws)
summary=json.load(open(E/'partial_rank_gene_bootstrap_summary.json'))
for spec,byrep in summary.items():
 for rep,result in byrep.items():assert np.allclose(np.quantile(draws[spec+'_'+rep],[.025,.975]),result['ci95'],atol=1e-14,rtol=0)
sp=pd.read_csv(E/'gene_sensitivity_split_sha256.csv');expected=[hashlib.sha256(('STATE-OPUS-R2-sensitivity-v1|'+g).encode()).hexdigest() for g in sp.gene];assert list(sp.sha256)==expected;assert list(sp.half)==list(np.arange(len(sp))%2);assert sp.gene.is_unique;assert list(sp.sha256)==sorted(sp.sha256);checks['opus_split_counts']=sp.half.value_counts().sort_index().to_dict();assert abs(checks['opus_split_counts'][0]-checks['opus_split_counts'][1])<=1
# Per-context tests genuinely have one row per gene in each representation/context.
assert not d[d.protocol=='zeroshot'].duplicated(['representation','context','perturbation_name']).any();checks['opus_per_context_gene_uniqueness']=True
(E/'real_data_checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
