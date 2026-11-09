"""Run actual STATE Codex-r1 analyses from verified new condition reductions.

Scientific inputs are computed from original DE rows by build_scores.py and
from original atlas/metadata sources by build_features.py. Historical aggregate
tables are comparison targets only, never inputs to estimated statistics.
"""
from __future__ import annotations
import argparse,hashlib,json,platform,time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import reconstruct as r

POLICY={
 'policy_fixed_before_results':True,
 'axis_z_scope':'all_rows',
 'axis_z_reason':'Inherit surviving original04: mean/sample SD over all released score rows before completeness filtering.',
 'bootstrap_seed':20260714,
 'bootstrap_seed_reason':'Inherit initial original04 seed; final continuation seed was not recovered.',
 'bootstrap_reps':10000,
 'bootstrap_reps_reason':'Documented final S-phase count; same fixed count used for all reconstructed intervals.',
 'bootstrap_pairing':'Identical parent-compound multinomial multiplicities for STATE and identity reference.',
 'matching':'Recovered original sensitivity: eight effect_q_1..4/cells_q_1..4 quintile indicators, all rows retained, original within-target OLS. Cutpoint scope inferred once as within current analysis partition, shared across contexts.',
 'sensitivity_standardization':'Retain the full released-panel axis scale when subsetting doses, contexts or partitions.',
 'no_result_tuning':True,
}
RUNS={'distance':'hvg_best','s_phase':'se_best','lineage':'se_last'}
HISTORICAL={
 'distance':{'state_raw':-.03221,'state_adjusted':-.15004,'identity_raw':.16321,'matched':-.12478,'ccle_adjusted':-.12962,'ccle_exact_adjusted':-.07886,'disposition':'negative: STATE error decreases along the frozen distance axis'},
 's_phase':{'state_raw':.08056,'state_adjusted':.09515,'identity_raw':-.03870,'paired':.11927,'matched':.10494,'rho':.30,'disposition':'negative: positive regression but context ordering fails frozen rho >= 0.70'},
 'lineage':{'state_adjusted':.03223,'paired':.01266,'rho':.82078,'hvg_discovery_adjusted':-.07233,'exclude_HepG2_adjusted':-.01196,'dose_5_adjusted':.01027,'disposition':'negative: unstable dose/context sensitivities and qualified prospectivity'},
}

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()

def identity(p):return {'bytes':p.stat().st_size,'sha256':sha256(p)}

def safe_json(value):
 if isinstance(value,dict):return {str(k):safe_json(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [safe_json(v) for v in value]
 if isinstance(value,np.ndarray):return safe_json(value.tolist())
 if isinstance(value,(np.integer,)):return int(value)
 if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
 if isinstance(value,(np.bool_,)):return bool(value)
 return value

def dump(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 temp=path.with_name(path.name+'.part');temp.write_text(json.dumps(safe_json(value),indent=2,allow_nan=False)+'\n');temp.replace(path)

def validated_receipt(path,root,manifest_hash,*,kind=None):
 if not path.is_file():raise FileNotFoundError(f'Required completed stage receipt is missing: {path}')
 d=json.loads(path.read_text())
 if not d.get('completed',d.get('status') in ['completed','computed','verified']):raise ValueError(f'Incomplete stage receipt: {path}')
 if d.get('source_manifest_sha256')!=manifest_hash:raise ValueError(f'Source manifest changed since stage was computed: {path}')
 if kind and d.get('reduction')!=kind:raise ValueError(f'Wrong scientific reduction kind: {path}')
 methods=d.get('method_sha256',{})
 if not methods:raise ValueError(f'Method hashes absent: {path}')
 for rel,h in methods.items():
  f=root/rel
  if not f.is_file() or sha256(f)!=h:raise ValueError(f'Stage method changed: {rel}')
 outputs=d.get('outputs',{})
 if not outputs:raise ValueError(f'Stage has no verified outputs: {path}')
 for rel,expected in outputs.items():
  f=root/rel
  if not f.is_file() or identity(f)!=expected:raise ValueError(f'Computed output missing or changed: {f}')
 return d

def load_scores(directory):
 pieces=[]
 for cell,stem in r.original_scoring().CONTEXT_FILES.items():
  lfc=pd.read_csv(directory/f'{stem}_lfc.csv')
  released=pd.read_csv(directory/f'{stem}_results.csv').rename(columns={'perturbation':'target'})
  if set(lfc.target)!=set(released.target):raise ValueError(f'Score/released target mismatch: {cell}')
  merged=released.merge(lfc,on='target',validate='one_to_one');merged['cell_line']=cell;pieces.append(merged)
 return pd.concat(pieces,ignore_index=True)

def validated_features(features,root):
 """Use the builder's exact source/method/output contract for both stages."""
 import build_features as b
 receipts=[];metadata=[]
 for stage,needed in [('obs',[b.OBS]),('expression',b.EXPRESSION)]:
  path=features/(stage+'_receipt.json')
  sources=b.source_entries(root,needed)
  if not b.cache_valid(path,features,sources,b.method_hashes(root)):
   raise ValueError(f'Original-source feature stage is absent or changed: {path}; run build_features.py first')
  doc=json.loads(path.read_text())
  if doc.get('scientific_execution')!='recomputed_from_verified_public_source_bytes':raise ValueError(f'Not an actual feature construction receipt: {path}')
  verified=doc.get('verified_inputs',[])
  if len(verified)!=len(sources) or not all(x.get('verified') and x.get('actual_sha256')==x.get('sha256') for x in verified):raise ValueError(f'Feature input verification is incomplete: {path}')
  receipts.append(path);metadata.append(doc)
 return receipts,metadata

def curve_plot(table,path,title):
 import matplotlib
 matplotlib.use('Agg')
 from matplotlib import pyplot as plt
 fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
 for stem,label,color in [('state','STATE','#8B1E3F'),('identity','Zero-effect reference','#367588')]:
  y=table[f'{stem}_rmse_mean'].to_numpy();lo=table[f'{stem}_rmse_ci_low'].to_numpy();hi=table[f'{stem}_rmse_ci_high'].to_numpy()
  ax.errorbar(table.distance,y,yerr=np.stack([y-lo,hi-y]),label=label,color=color,marker='o',capsize=3)
 for row in table.itertuples():ax.annotate(row.cell_line,(row.distance,row.state_rmse_mean),xytext=(4,5),textcoords='offset points',fontsize=8)
 ax.set(title=title,xlabel='Recomputed axis value',ylabel='Log2 fold-change RMSE');ax.legend(frameon=False);fig.savefig(path,dpi=160);plt.close(fig)

def append_comparison(rows,axis,metric,historical,actual,tolerance=5e-5,note='Reported rounded value; no calculation choice is changed to obtain agreement.'):
 rows.append({'axis':axis,'metric':metric,'historical':historical,'recomputed':actual,'difference':actual-historical,'tolerance':tolerance,'within_tolerance':abs(actual-historical)<=tolerance if tolerance is not None else None,'note':note})

def run(root,inputs=None,features=None,output=None,force=False):
 root=Path(root).resolve();features=Path(features or root/'computed/features').resolve();output=Path(output or root/'computed/analysis').resolve();inputs=Path(inputs or root/'inputs').resolve()
 started=time.time();manifest=root/'methods/sources.json';manifest_hash=sha256(manifest)
 source_receipt=root/'computed/scores/score_receipt.json'
 score_meta=validated_receipt(source_receipt,root,manifest_hash,kind='actual_original_DE_rows')
 if score_meta.get('condition_tables')!=15:raise ValueError('Need all15 actual condition-table reductions')
 feature_receipts,feature_meta=validated_features(features,root)
 stage_hashes={str(p.relative_to(root)):sha256(p) for p in [source_receipt,*feature_receipts]}
 method_paths=['methods/run_analysis.py','methods/reconstruct.py','methods/original/04_analyze_frozen_axis.py']
 method_hashes={p:sha256(root/p) for p in method_paths}
 receipt_path=output/'analysis_receipt.json'
 if not force and receipt_path.exists():
  old=json.loads(receipt_path.read_text())
  if old.get('completed') and old.get('source_manifest_sha256')==manifest_hash and old.get('method_sha256')==method_hashes and old.get('stage_receipt_sha256')==stage_hashes and old.get('policy')==POLICY:
   if all((root/p).is_file() and identity(root/p)==meta for p,meta in old.get('outputs',{}).items()) and old.get('outputs'):
    print('Verified existing scientific analysis cache; no historical aggregate substitution.',flush=True);return old
 output.mkdir(parents=True,exist_ok=True)
 dump(output/'reconstruction_policy.json',POLICY)
 counts=pd.read_csv(features/'cell_counts.csv')
 primary=pd.read_csv(features/'primary_cmp_distances.csv')
 ccle=pd.read_csv(features/'independent_ccle_distances.csv')
 sphase=pd.read_csv(features/'s_phase_features.csv')
 lineage=pd.read_csv(features/'lineage_features.csv')
 axes={'distance':primary.rename(columns={'distance':'axis_value'}),'s_phase':sphase,'lineage':lineage}
 scored={key:load_scores(root/'computed/scores'/key) for key in RUNS.values()}
 comparisons=[];conditions_by_axis={};results={};sensitivity=[];all_curves={}
 for axis_name,run_name in RUNS.items():
  print(f'Analyzing {axis_name} from {run_name} actual condition records',flush=True)
  dest=output/axis_name;dest.mkdir(parents=True,exist_ok=True)
  conditions,eligibility,all_rows=r.build_condition_table(root/'computed/scores'/run_name,root/'computed/scores'/run_name,counts,axes[axis_name],axis_z_scope=POLICY['axis_z_scope'],scored_rows=scored[run_name])
  conditions.to_csv(dest/'per_condition_scores.csv',index=False);eligibility.reset_index().to_csv(dest/'compound_eligibility.csv',index=False)
  conditions_by_axis[axis_name]=conditions
  doc={'axis':axis_name,'run':run_name,'policy':POLICY,'historical_decision':HISTORICAL[axis_name]['disposition'],'historical_decision_is_not_recomputed_outcome':True,'partitions':{}}
  for part in ['discovery','confirmation','all']:
   print(f'  {axis_name}/{part}: fitting,10,000 paired compound bootstraps',flush=True)
   res,spc=r.analyze_axis(conditions,seed=POLICY['bootstrap_seed'],reps=POLICY['bootstrap_reps'],partition=part)
   sub=conditions if part=='all' else conditions.loc[conditions.partition==part]
   matching,matched,strata=r.quintile_matching(sub);res['matching_reconstructed']=matching
   doc['partitions'][part]=res
   if part=='confirmation':
    spc.to_csv(dest/'spc_table.csv',index=False);all_curves[axis_name]=spc
    matched.to_csv(dest/'matching_weights.csv',index=False);strata.reset_index().to_csv(dest/'matching_strata.csv',index=False)
    curve_plot(spc,dest/'spc.png',axis_name.replace('_',' ').title()+' — recomputed confirmation')
   for name,value in res['dose_sensitivity'].items():sensitivity.append({'axis':axis_name,'partition':part,'kind':'dose','subset':name,**value})
   for name,value in res['leave_one_context_out'].items():sensitivity.append({'axis':axis_name,'partition':part,'kind':'leave_one_context_out','subset':name,**value})
  conf=doc['partitions']['confirmation'];historical=HISTORICAL[axis_name]
  for metric in ['state_raw','state_adjusted','identity_raw']:
   if metric in historical:append_comparison(comparisons,axis_name,metric,historical[metric],conf['models'][metric]['estimate'])
  if 'paired' in historical:append_comparison(comparisons,axis_name,'paired_state_minus_identity',historical['paired'],conf['paired_state_minus_identity']['estimate'])
  if 'rho' in historical:append_comparison(comparisons,axis_name,'context_spearman',historical['rho'],conf['context_spearman'])
  if 'matched' in historical and conf['matching_reconstructed'].get('status')=='computed':append_comparison(comparisons,axis_name,'quintile_matching',historical['matched'],conf['matching_reconstructed']['estimate'],None,'Original eight quintile-control columns and full-row inclusion recovered; partition-specific cutpoint scope is an explicit reconstruction assumption.')
  for metric,value in [('rows',4020),('targets',804),('compounds',268),('contexts',5)]:append_comparison(comparisons,axis_name,'confirmation_'+metric,value,conf['counts'][metric],0)
  doc['computed_diagnostics']={'state_raw_positive':conf['models']['state_raw']['estimate']>0,'state_adjusted_positive':conf['models']['state_adjusted']['estimate']>0,'context_order_rho_at_least_point70':conf['context_spearman']>=.70,'all_dose_adjusted_positive':all(v['estimate']>0 for v in conf['dose_sensitivity'].values()),'all_leave_one_context_out_adjusted_positive':all(v['estimate']>0 for v in conf['leave_one_context_out'].values())}
  results[axis_name]=doc;dump(dest/'analysis.json',doc)
 # Independent atlas uses the original shared axis standardization population.
 distance_conditions,_,_=r.build_condition_table(root/'computed/scores/hvg_best',root/'computed/scores/hvg_best',counts,ccle.rename(columns={'distance':'axis_value'}),axis_z_scope=POLICY['axis_z_scope'],scored_rows=scored['hvg_best'])
 for key,c in [('ccle',distance_conditions),('ccle_exact_contexts',distance_conditions.loc[~distance_conditions.proxy_used.astype(bool)].copy())]:
  res,spc=r.analyze_axis(c,seed=POLICY['bootstrap_seed'],reps=POLICY['bootstrap_reps'])
  dump(output/'distance'/f'{key}_analysis.json',res);spc.to_csv(output/'distance'/f'{key}_spc_table.csv',index=False)
  append_comparison(comparisons,'distance',key+'_adjusted',HISTORICAL['distance']['ccle_adjusted' if key=='ccle' else 'ccle_exact_adjusted'],res['models']['state_adjusted']['estimate'])
 # Later hypotheses were discovered/screened on HVG discovery, not SE confirmation.
 for axis_name in ['s_phase','lineage']:
  c,_,_=r.build_condition_table(root/'computed/scores/hvg_best',root/'computed/scores/hvg_best',counts,axes[axis_name],axis_z_scope=POLICY['axis_z_scope'],scored_rows=scored['hvg_best'])
  res,spc=r.analyze_axis(c,seed=POLICY['bootstrap_seed'],reps=POLICY['bootstrap_reps'],partition='discovery')
  dump(output/axis_name/'hvg_discovery_analysis.json',res);spc.to_csv(output/axis_name/'hvg_discovery_spc.csv',index=False)
  if axis_name=='lineage':append_comparison(comparisons,axis_name,'hvg_discovery_adjusted',HISTORICAL[axis_name]['hvg_discovery_adjusted'],res['models']['state_adjusted']['estimate'])
 # Original discovery screen: native911/915 used unweighted condition means.
 control_dir=output/'controls';control_dir.mkdir(parents=True,exist_ok=True)
 baseline=pd.read_csv(features/'baseline_heterogeneity.csv').set_index('cell_line')
 discovery=conditions_by_axis['distance'].query("partition == 'discovery'").groupby('cell_line').state_lfc_rmse.mean()
 baseline['state_rmse_discovery']=discovery;baseline.to_csv(control_dir/'baseline_discovery_features.csv')
 screen=[]
 for col in ['gene_mean','gene_sd','tscp_mean','tscp_sd','mito_mean','mito_sd','S_sd','G2M_sd','phase_entropy']:
  z=baseline[[col,'state_rmse_discovery']].dropna();test=spearmanr(z[col],z.state_rmse_discovery)
  screen.append({'feature':col,'n_contexts':len(z),'spearman_rho':float(test.statistic),'two_sided_p':float(test.pvalue)})
 pd.DataFrame(screen).to_csv(control_dir/'baseline_discovery_screen.csv',index=False)
 pd.DataFrame(sensitivity).to_csv(control_dir/'all_sensitivity_estimates.csv',index=False)
 count_rows=[]
 for axis_name,c in conditions_by_axis.items():
  for part in ['discovery','confirmation','all']:
   z=c if part=='all' else c[c.partition==part]
   count_rows.append({'axis':axis_name,'partition':part,'rows':len(z),'targets':z.target.nunique(),'compounds':z.compound.nunique(),'contexts':z.cell_line.nunique(),'min_cells':z.n_cells.min(),'median_cells':z.n_cells.median(),'max_cells':z.n_cells.max()})
 pd.DataFrame(count_rows).to_csv(control_dir/'source_axis_counts.csv',index=False)
 all_conditions=pd.concat([c.assign(axis=name,run=RUNS[name]) for name,c in conditions_by_axis.items()],ignore_index=True)
 all_conditions.to_csv(control_dir/'per_condition_scores.csv',index=False)
 control_doc={'policy':POLICY,'controls':r.CONTROLS,'cell_count_rule':'full-QC cells when positive, otherwise all observed cells','axes':{name:doc['partitions']['confirmation'] for name,doc in results.items()},'historical_interpretation':'Controls did not rescue the failed original distance, S-phase shape or lineage stability findings; reconstructed matching is labeled separately.'}
 dump(control_dir/'analysis.json',control_doc)
 import matplotlib
 matplotlib.use('Agg')
 from matplotlib import pyplot as plt
 fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained');positions=np.arange(3)
 for shift,key,label in [(-.12,'state_raw','Raw STATE slope'),(.12,'state_adjusted','Adjusted STATE slope')]:
  vals=[results[n]['partitions']['confirmation']['models'][key] for n in RUNS]
  y=np.array([v['estimate'] for v in vals]);lo=np.array([v['bootstrap_ci95'][0] for v in vals]);hi=np.array([v['bootstrap_ci95'][1] for v in vals])
  ax.errorbar(positions+shift,y,yerr=np.maximum(0,np.stack([y-lo,hi-y])),fmt='o',capsize=3,label=label)
 ax.axhline(0,color='black',lw=.8);ax.set_xticks(positions,[n.replace('_',' ') for n in RUNS]);ax.set(ylabel='RMSE slope per axis SD',title='Recomputed continuous-control sensitivity');ax.legend(frameon=False);fig.savefig(control_dir/'spc.png',dpi=160);plt.close(fig)
 lineage_conf=results['lineage']['partitions']['confirmation']
 append_comparison(comparisons,'lineage','exclude_HepG2_adjusted',HISTORICAL['lineage']['exclude_HepG2_adjusted'],lineage_conf['leave_one_context_out']['HepG2/C3A']['estimate'])
 append_comparison(comparisons,'lineage','dose_5_adjusted',HISTORICAL['lineage']['dose_5_adjusted'],lineage_conf['dose_sensitivity']['5.0']['estimate'])
 # Saved historical per-context tables are comparison targets only, after all fits.
 history=root/'recovery/original_handoff/supporting/results'
 for axis_name,relative in [('distance','spc_table.csv'),('s_phase','st_se_confirmation/spc_table.csv'),('lineage','lineage_followup/spc_table.csv')]:
  p=history/relative
  if p.is_file() and p.stat().st_size:
   old=pd.read_csv(p).set_index('cell_line');new=all_curves[axis_name].set_index('cell_line')
   for cell in old.index:
    for col in ['state_rmse_mean','identity_rmse_mean']:
     append_comparison(comparisons,axis_name,f'{cell}/{col}',float(old.loc[cell,col]),float(new.loc[cell,col]),1e-9,'Original aggregate is used only as an independent comparison target after per-condition computation.')
 comparison=pd.DataFrame(comparisons);comparison.to_csv(output/'historical_comparison.csv',index=False)
 comparison.to_csv(control_dir/'historical_comparison.csv',index=False)
 methods_versions={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__}
 outputs={str(p.relative_to(root)):identity(p) for p in output.rglob('*') if p.is_file() and p!=receipt_path and not p.name.endswith('.part')}
 receipt={'completed':True,'scientific_workflow_executed':True,'input_kind':'original public DE rows and original atlas/observation metadata; verified upstream computation receipts','historical_aggregate_fallback':False,'source_manifest_sha256':manifest_hash,'method_sha256':method_hashes,'stage_receipt_sha256':stage_hashes,'policy':POLICY,'versions':methods_versions,'outputs':outputs,'historical_comparisons':len(comparison),'elapsed_seconds':round(time.time()-started,3)}
 dump(receipt_path,receipt);print(json.dumps({'completed':True,'output':str(output),'comparisons':len(comparison),'seconds':receipt['elapsed_seconds']}),flush=True);return receipt

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--inputs',type=Path);p.add_argument('--features',type=Path);p.add_argument('--output',type=Path);p.add_argument('--force',action='store_true');a=p.parse_args();run(a.root,a.inputs,a.features,a.output,a.force)
if __name__=='__main__':main()
