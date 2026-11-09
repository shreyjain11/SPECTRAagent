"""Run the preserved ESMFold2 scientific analyses on explicitly supplied new outputs.

The archive supplies frozen cohorts, metadata, split definitions and original code.
It never supplies outcomes to a requested fresh run. Validation fixtures must be
staged explicitly by validate_original_workflow.py and are labelled retained replay.
"""
from pathlib import Path
from contextlib import contextmanager, redirect_stdout
import hashlib, importlib.util, io, json, os, shutil, sys
import numpy as np
import pandas as pd

BUNDLE=Path(__file__).resolve().parent
RUNS=BUNDLE/'original_runs'
NAMES={
 'single':'esmfold2_single_controller_final_run',
 'beyond':'esmfold2_beyond_evolutionary_support_final_run',
 'geometry':'esmfold2_new_axes_after_scaling_external_20260531T193531Z',
 'shared':'esmfold2_shared_axis_cameo_rcsb_20260601T173500Z',
 'acid':'esmfold2_all_evidence_confirmation_loop_20260601T215426Z',
 'cys':'esmfold2_all_scored_evidence_loop_20260601T230100Z',
 'global':'esmfold2_global_hypothesis_audit_20260602',
 'proxy':'esmfold2_cys_proxy_axis_iteration_20260602',
 'envelope':'esmfold2_envelope_fusion_axis_confirmation_20260602',
}
METRICS={'sample_index','status','error','wall_sec','wall_sec_target_all_samples','seed','num_loops','num_sampling_steps','num_diffusion_samples','ptm','plddt_mean','plddt_ca_mean','alignment_identity','alignment_coverage','aligned_ca','ca_lddt','ca_rmsd','gdt_ts','ca_median_error','ca_p90_error','baseline_ca_lddt','baseline_gdt_ts','baseline_ca_rmsd','scaled_mean_ca_lddt','scaled_sd_ca_lddt','scaled_n_samples','scaled_mean_gdt_ts','scaled_mean_ptm'}
# Metadata availability is part of each historical analysis join. More complete
# metadata from another panel must not fill that analysis's originally missing fields.
FROZEN_METADATA={'organism','method','resolution','title','keywords','entity_description','query_hits',
 'release_date','submission_date','polymer_type','rcsb_entity_id','rcsb_instance_id',
 'entry_id','entity_id','asym_id','auth_asym_id','source','feature_panel','result_panel',
 'inference_setting','evidence_source','dataset','analysis_id','combined_row_id',
 'run_dir','run_name','result_file','data_family','quaternary_state','difficulty'}

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def dump(path,value):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n');return str(p)
def read(path):return pd.read_csv(path,low_memory=False)
def module(group,filename):
 import acquisition as a
 p=RUNS/NAMES.get(group,group)/('scripts/'+filename if '/' not in filename and filename!='iterate_proxy_axes.py' else filename)
 return a._module(p)
def overlay(base,generated):
 """Align by target, use generated values (including NaNs), preserve cohort order."""
 if generated.target_id.duplicated().any():raise ValueError('Duplicate generated target IDs')
 g=generated.set_index('target_id');out=base.copy()
 missing=set(out.target_id)-set(g.index)
 if missing:raise ValueError('Missing rebuilt targets: '+str(sorted(missing)[:12]))
 updates={col:out.target_id.map(g[col]).to_numpy() for col in g if col not in METRICS}
 return pd.concat([out.drop(columns=list(updates),errors='ignore').reset_index(drop=True),pd.DataFrame(updates)],axis=1)

def rebuild_features(axis,workspace):
 """Materialize scoring inputs from exact downloaded references/MSAs and frozen metadata."""
 import acquisition as a
 w=Path(workspace).resolve();prepared=a.prepare_inputs(axis,w,require_downloads=True,reset=True)
 seqmod=module('beyond','build_nonerror_features.py')
 shared=module('shared','analyze_shared_axes.py')
 ext=module('geometry','build_combined_and_score_axes.py')
 expanded=module('cys','expand_all_scored_features.py')
 # Full original 141-target reference fit is immutable even in notebooks using only a subset.
 frozen=read(RUNS/NAMES['beyond']/'spectra_ready_dataset/prospective_features.followup.csv')
 original_reference=frozen.copy()
 core=None
 if 'cameo' in prepared:
  cb=module('single','build_cameo_dataset.py');cb.ROOT=w;cb.RAW=w/'downloads/cameo';cb.OUT=w/'reconstructed/cameo'
  meta=read(cb.RAW/'meta.csv')
  class Train:
   def to_pandas(self):return meta.copy()
  cb.load_dataset=lambda *args,**kwargs:{'train':Train()}
  cb.main();core=read(cb.OUT/'candidate_features.csv')
  for col in ['pdb_path','msa_path']:
   core[col]=core[col].map(lambda p:str(w/p) if isinstance(p,str) and p else '')
  archive=read(a.BUNDLE/a.MANIFEST['panels']['cameo']['source_features'])
  assert set(core.target_id)==set(archive.target_id)
  expected=archive.set_index('target_id').sequence
  if not core.apply(lambda r:r.sequence==expected[r.target_id],axis=1).all():raise ValueError('Downloaded FASTA differs from frozen sequences')
  frozen=overlay(frozen,core)
  generated=pd.DataFrame([seqmod.sequence_features(s) for s in frozen.sequence]);generated.insert(0,'target_id',frozen.target_id)
  frozen=overlay(frozen,generated)
  geometry=pd.DataFrame([seqmod.reference_structure_features(r) for _,r in frozen.iterrows()]);geometry.insert(0,'target_id',frozen.target_id)
  # Original parser behavior, including missing geometry values, is preserved.
  frozen=overlay(frozen,geometry)
  freeze=module('beyond','freeze_followup_axes.py')
  frozen['flexible_nonhelical_composite_rank']=freeze.rank_mean(frozen,['proline_fraction','chou_beta_minus_helix','chou_turn_minus_helix'])
  frozen['nonhelical_topology_composite_rank']=freeze.rank_mean(frozen,['chou_beta_minus_helix','chou_turn_minus_helix'])
  # Historical frozen memberships remain the original fit; do not refit qcut on a test panel.
  for col in original_reference:
   if col.startswith('axis_'):frozen[col]=frozen.target_id.map(original_reference.set_index('target_id')[col])
  (w/'reconstructed').mkdir(exist_ok=True);frozen.to_csv(w/'reconstructed/cameo_followup_features.csv',index=False)
 prior_path=w/'feature_reconstruction_report.json'
 receipt=json.loads(prior_path.read_text()) if prior_path.exists() else {'panels':{}}
 prior_panels=receipt.get('panels',{})
 receipt={'axis':int(axis),'mode':'downloaded_raw_reconstruction','panels':prior_panels,'frozen_fit':'Original cohort IDs, metadata and frozen axis memberships retained; feature values rebuilt. Original 8S7A_A level4 remains authoritative.'}
 for name,info in prepared.items():
  df=read(info['features']);old=df.copy()
  if name.startswith('cameo') and core is not None:
   df=overlay(df,frozen[frozen.target_id.isin(df.target_id)])
  values=pd.DataFrame([seqmod.sequence_features(s) for s in df.sequence]);values.insert(0,'target_id',df.target_id);df=overlay(df,values)
  extra=pd.DataFrame([shared.sequence_features(s) for s in df.sequence]);extra.insert(0,'target_id',df.target_id);df=overlay(df,extra)
  df['seq_len']=df.sequence.str.len()
  # The original cross-source/common derived features and external geometry parser.
  if name=='external34':df=ext.add_external_topology(df,w)
  df=ext.ensure_sequence_features(df)
  df=ext.add_common_derived(df,float(frozen.seq_len.median()))
  df=expanded.add_expanded_features(df)
  if name=='acidic78':
   df['acidic_window_feature']=df.max_negative_charge_window31
   df['acidic_window_stress']=-df.max_negative_charge_window31
  if not name.startswith('cameo') and 'flexible_nonhelical_composite_rank' in old:
   eb=module('beyond','external_rcsb_same_bucket_expansion_20260531/scripts/build_external_rcsb_bucket_panel.py')
   cols=['proline_fraction','chou_beta_minus_helix','chou_turn_minus_helix']
   for col in cols:df[col+'_prior_pct']=df[col].map(lambda x:eb.empirical_pct(original_reference[col],x))
   df['flexible_nonhelical_composite_rank']=df[[c+'_prior_pct' for c in cols]].mean(axis=1)
  if name in ['viral36','envelope38','surface45']:
   b=module('envelope','build_surface_lowhelical_confirmation_panel.py')
   df['disulfide_capacity_per100']=df.sequence.map(b.disulfide_capacity_per100);df['tm_helix_proxy_calc']=df.sequence.map(b.tm_proxy);df['nglyc_motif_count']=df.sequence.map(b.nglyc_count)
   if name=='surface45':df=overlay(df,pd.DataFrame([dict(target_id=r['target_id'],**b.axis_features(r)) for r in df.to_dict('records')]))
   elif name=='envelope38':df['envelope_fusion_score']=df.apply(module('envelope','build_envelope_fusion_confirmation_panel.py').level,axis=1)
   else:
    v=module(a.MANIFEST['panels'][name]['source_run_root'].split('/')[-1],'build_viral_disulfide_pilot_panel.py')
    df['viral_disulfide_capacity_per100']=df.sequence.map(v.disulfide_capacity_per100);df['viral_disulfide_score']=df.apply(v.axis_score,axis=1)
  # Frozen labels for candidate-selected cohorts are part of the original design.
  for col in old:
   if col.startswith('axis_') or col in ['external_axis_level','charge_level','acidic_window_level','cys_level']:
    df[col]=old[col].to_numpy()
  df=df.drop(columns=[c for c in METRICS if c in df],errors='ignore')
  df.to_csv(info['features'],index=False)
  receipt['panels'][name]={'features':info['features'],'sha256':digest(info['features']),'rows':len(df),'recomputed_columns':sorted(set(values.columns)|set(extra.columns)|{'seq_len'}),'geometry_rebuilt':name.startswith('cameo') or name=='external34'}
 dump(w/'feature_reconstruction_report.json',receipt);return receipt

def require_features(axis,workspace):
 import acquisition as a
 w=Path(workspace);p=w/'feature_reconstruction_report.json'
 if not p.is_file():raise FileNotFoundError('Run input reconstruction before inference/analysis: '+str(p))
 receipt=json.loads(p.read_text());out={}
 for name in a.panels_for(axis):
  if name not in receipt.get('panels',{}):raise ValueError('Missing reconstructed panel '+name)
  item=receipt['panels'][name];f=w/'panels'/name/'features.csv'
  if not f.is_file() or digest(f)!=item['sha256']:raise ValueError('Reconstructed features missing or changed: '+str(f))
  out[name]={'features':str(f),'results':str(f.parent/'target_model_results.csv'),'n_original_targets':item['rows']}
 return out

def validate_results(axis,workspace):
 """Require complete attempted targets, explicit failures and finite successful scores."""
 import acquisition as a
 prepared=require_features(axis,workspace);checks={}
 for name,info in prepared.items():
  p=Path(info['results'])
  if not p.is_file():raise FileNotFoundError('Inference results missing for '+name+': '+str(p))
  f=read(info['features']);r=read(p);settings=a.MANIFEST['panels'][name]['inference']
  eligible=f.seq_len.le(settings['max_len'])
  if 'eligible_reference' in f:eligible &= f.eligible_reference.fillna(False).astype(bool)
  expected=set(f.loc[eligible,'target_id']);observed=set(r.target_id)
  if expected-observed:raise ValueError('Incomplete '+name+' results: '+str(sorted(expected-observed)))
  if observed-set(f.target_id):raise ValueError('Unexpected result targets in '+name)
  ok=r.status.eq('ok')
  # The original CA-lDDT returns NaN when no eligible reference pairs exist (historical9RYJ_1).
  # Keep that scientific behavior, report exclusions explicitly, and never treat all-nonfinite as complete.
  if not r.loc[ok,'ca_lddt'].notna().any():raise ValueError('No finite successful accuracy values in '+name)
  n=settings['num_diffusion_samples']
  if n>1:
   for target,g in r.groupby('target_id'):
    if g.status.eq('ok').any() and set(pd.to_numeric(g.sample_index,errors='coerce').dropna().astype(int))!=set(range(n)):
     raise ValueError('Incomplete sample set: '+name+'/'+str(target))
  checks[name]={'rows':len(r),'successful_rows':int(ok.sum()),'failed_rows':int((~ok).sum()),'nonfinite_accuracy_rows':int(r.ca_lddt.isna().sum()),'result_sha256':digest(p),'features_sha256':digest(info['features'])}
  if not ok.any():raise ValueError('No successful model evaluations in '+name)
 dump(Path(workspace)/'result_completeness.json',checks);return checks

def select(r,policy='best_by_ptm'):
 """Shared early-panel rule; later panels use their own original selector."""
 if 'sample_index' not in r:return r.drop_duplicates('target_id').copy()
 sample=pd.to_numeric(r.sample_index,errors='coerce')
 ok=r[r.status.fillna('ok').eq('ok') & sample.ge(0)].copy()
 if policy=='first_sample':return ok[pd.to_numeric(ok.sample_index,errors='coerce').eq(0)].copy()
 col={'best_by_ptm':'ptm','best_by_plddt':'plddt_mean','oracle_best_ca_lddt':'ca_lddt'}[policy]
 ok[col]=pd.to_numeric(ok[col],errors='coerce')
 return ok.sort_values(['target_id',col,'sample_index'],ascending=[True,False,True]).groupby('target_id',as_index=False).head(1)

def global_select(r):
 """The original global audit's pTM then pLDDT normalization rule."""
 if 'sample_index' not in r:return r.copy()
 out=r.copy();sort_cols=[]
 for col,key in [('ptm','_ptm_sort'),('plddt_mean','_plddt_sort')]:
  if col in out:
   out[key]=pd.to_numeric(out[col],errors='coerce').fillna(-1);sort_cols.append(key)
 keys=['target_id']+(['sequence'] if 'sequence' in out else [])
 if sort_cols:out=out.sort_values(sort_cols,ascending=False)
 out=out.drop_duplicates(keys,keep='first');out['selection']='best_by_ptm'
 return out

class Analysis:
 def __init__(self,axis,workspace):
  import acquisition as a
  self.a=a;self.axis=int(axis);self.w=Path(workspace).resolve();self.out=self.w/'analysis'/f'axis-{self.axis:02}';self.out.mkdir(parents=True,exist_ok=True)
  self.checks=validate_results(axis,self.w);self.f={};self.r={};self.selected={};self.artifacts={}
  for name,info in require_features(axis,self.w).items():
   self.f[name]=read(info['features']);self.r[name]=read(info['results']);self.selected[name]=select(self.r[name]).set_index('target_id')
 def save(self,name,value):
  p=self.out/name;p.parent.mkdir(parents=True,exist_ok=True)
  if isinstance(value,pd.DataFrame):value.to_csv(p,index=False)
  else:dump(p,value)
  self.artifacts[name]=str(p);return p
 def panel_for(self,row):
  target=row['target_id'];text=' '.join(str(row.get(k,'')) for k in ['result_file','evidence_source','target_result_origin','feature_panel','result_panel','dataset','evaluation_pool','inference_setting','source','source_group','panel']).lower()
  rules=[(['surface_lowhelical'],'surface45'),(['envelope_fusion'],'envelope38'),(['viral_disulfide'],'viral36'),(['cys_confirmation','cysteine','fresh_cys','all_scored_evidence'],'cysteine95'),(['acidic_window'],'acidic78'),(['fresh_charge','charge_confirmation','charge_axis_fresh'],'charge97'),(['expanded_107','flexible_axis_expanded'],'flexible107'),(['original_34','external_rcsb_same_bucket','external_rcsb'],'external34'),(['5seeds'],'cameo_scaled14'),(['cameo_scaled','scaled_matched','top_tail','5samples_full'],'cameo_scaled40'),(['cameo','single_controller','beyond_evolutionary_support_20260531'],'cameo')]
  for words,name in rules:
   if any(k in text for k in words) and name in self.f and target in set(self.f[name].target_id):return name
  candidates=[n for n,f in self.f.items() if target in set(f.target_id)]
  if len(candidates)==1:return candidates[0]
  if 'rcsb_scaled_combined' in text:
   for n in ['flexible107','external34']:
    if n in candidates:return n
  raise ValueError('Ambiguous/missing outcome lineage for '+str(target)+': '+str(candidates)+' '+text)
 def joined(self,name,policy='best_by_ptm'):
  f=self.f[name].drop(columns=list(METRICS),errors='ignore');r=select(self.r[name],policy)
  return f.merge(r,on='target_id',how='inner',suffixes=('','_metric'),validate='one_to_one')
 def refresh(self,template):
  rows=[]
  for _,row in template.iterrows():
   if str(row.get('evidence_source',''))=='RCSB_scaled_combined':
    # The combined RCSB result is selected across both panels each time.
    # Its archived winning panel is an outcome, not frozen cohort metadata.
    combined=shared_frames(self)[0]
    current=combined[(combined.source=='RCSB') & (combined.target_id==row.target_id)]
    if len(current)!=1:raise ValueError('Missing/ambiguous regenerated shared RCSB target '+str(row.target_id))
    current=current.iloc[0];d=row.to_dict()
    for c in METRICS:
     if c in d:d[c]=np.nan
    for c,v in current.items():
     if (c in d or c in METRICS) and c not in ['evidence_source','evidence_root','analysis_id','combined_row_id']:d[c]=v
    d['_rerun_panel']={'original_34':'external34','expanded_107':'flexible107'}[current.result_panel]
    rows.append(d);continue
   name=self.panel_for(row);target=row.target_id;fresh=self.f[name].set_index('target_id').loc[target]
   d=row.to_dict()
   for c in fresh.index:
    if c not in METRICS and c in d and not c.startswith('axis_') and c not in FROZEN_METADATA:d[c]=fresh[c]
   for c in METRICS:
    if c in d:d[c]=np.nan
   selected=self.selected[name]
   if str(row.get('dataset','')) in ['cameo_scaled','external_rcsb']:
    # Geometry's original aggregator preserves file-order pTM ties and
    # recomputes per-target sample mean, deviation and count diagnostics.
    if not hasattr(self,'_geometry_selected'):self._geometry_selected={}
    if name not in self._geometry_selected:
     m=module('geometry','build_combined_and_score_axes.py')
     self._geometry_selected[name]=m.aggregate_scaled_results(self.w/'panels'/name/'target_model_results.csv',str(row.get('evaluation_pool',''))).set_index('target_id')
    selected=self._geometry_selected[name]
   if target not in selected.index:raise ValueError('Missing evaluated outcome '+name+'/'+target)
   d.update({c:v for c,v in selected.loc[target].items() if c in METRICS})
   d['_rerun_panel']=name;rows.append(d)
  return pd.DataFrame(rows)
 @contextmanager
 def cwd(self):
  old=Path.cwd();os.chdir(self.out)
  try:yield
  finally:os.chdir(old)
 def original_main(self,group,filename,overrides=None):
  m=module(group,filename);orig=RUNS/NAMES.get(group,group)
  for key,val in list(vars(m).items()):
   if isinstance(val,Path):
    text=str(val)
    if str(orig) in text:setattr(m,key,self.out/val.relative_to(orig))
    elif '/ewsc/yektefai/spectra_runs/'+NAMES.get(group,group) in text:setattr(m,key,self.out/text.split('/ewsc/yektefai/spectra_runs/'+NAMES.get(group,group)+'/',1)[-1])
  for k,v in (overrides or {}).items():setattr(m,k,v)
  with self.cwd(),redirect_stdout(io.StringIO()) as output:m.main()
  self.save(filename+'.stdout.txt',{'stdout':output.getvalue()})
  return m

def confirmation(job,name):
 panel=job.a.MANIFEST['panels'][name];group=panel['source_run_root'].split('/')[-1]
 specs={'flexible107':('summarize_expanded_external_spc.py','flex'),'charge97':('summarize_charge_confirmation.py','charge'),'acidic78':('summarize_acidic_window_confirmation.py','acid'),'cysteine95':('summarize_cys_confirmation.py','cys'),'viral36':('summarize_viral_disulfide_pilot.py','viral'),'envelope38':('summarize_envelope_fusion_confirmation.py','env'),'surface45':('summarize_surface_lowhelical_confirmation.py','surface')}
 filename,kind=specs[name];m=module(group,filename);curves=[];effects=[];targets=[]
 for policy in ['best_by_ptm','best_by_plddt','oracle_best_ca_lddt','first_sample']:
  f=job.f[name];r=job.r[name]
  if kind in ['flex','charge']:
   if policy=='first_sample':
    chosen=m.first_sample(r) if kind=='charge' else r[r.sample_index.eq(0)&r.status.eq('ok')].copy()
   else:chosen=m.best_by(r,{'best_by_ptm':'ptm','best_by_plddt':'plddt_mean','oracle_best_ca_lddt':'ca_lddt'}[policy])
   c,e=m.summarize(policy,chosen,f) if kind=='flex' else m.summarize_selection(policy,chosen,f)
   d=f.drop(columns=list(METRICS),errors='ignore').merge(chosen,on='target_id',how='inner',suffixes=('','_metric'),validate='one_to_one')
  elif kind in ['acid','env']:c,e,d=m.summarize_selection(f,r,policy)
  elif kind=='cys':d,c,e=m.summarize_policy(f,r,policy)
  elif kind=='viral':
   c,e=m.summarize_selection(f,r,policy)
   d=f.drop(columns=list(METRICS),errors='ignore').merge(m.select_rows(r,policy),on='target_id',how='inner',suffixes=('','_metric'),validate='one_to_one')
  else:c,e,d=m.summarize_policy(f,r,policy)
  c=c.copy();c['selection']=policy;d=d.copy();d['selection']=policy;curves.append(c);effects.append(e);targets.append(d)
 job.save(name+'_curves.csv',pd.concat(curves,ignore_index=True));job.save(name+'_effects.json',effects);job.save(name+'_target_level.csv',pd.concat(targets,ignore_index=True))

def cameo(job):
 f=job.f['cameo'].drop(columns=list(METRICS),errors='ignore');fp=job.save('cameo_features.csv',f);rp=job.save('cameo_results.csv',job.r['cameo'])
 job.original_main('single','finalize_spectra_outputs.py',{'ROOT':job.out,'FEATURES':fp,'RESULTS':rp})
 # Reports generated by old main contain old fixed prose. They remain diagnostic code output,
 # never a replacement for the historical agent decision presented by the notebook.
 for name in ['spectral_performance_curve.csv','control_analysis.json']:job.artifacts[name]=str(job.out/name)

def flexible(job):
 f=overlay(read(RUNS/NAMES['beyond']/'spectra_ready_dataset/prospective_features.followup.csv'),job.f['cameo'])
 # Scorers perform their own inner join to results; feature inputs contain no outcomes.
 fp=job.save('followup_features.csv',f.drop(columns=list(METRICS),errors='ignore'));rp=job.save('cameo_results.csv',job.r['cameo'])
 for filename,definition in [('score_axes.py','axis_definitions_prejoin.json'),('score_followup_axes.py','axis_definitions_followup.json')]:
  definition_path=job.out/definition;shutil.copyfile(RUNS/NAMES['beyond']/definition,definition_path)
  job.original_main('beyond',filename,{'ROOT':job.out,'FEATURE_CSV':fp,'RESULTS_CSV':rp,'AXIS_JSON':definition_path})
 for name in ['spectral_curves_all_axes.csv','axis_summary.csv','followup_axis_curves.csv','followup_axis_summary.csv','control_analysis.json']:job.artifacts[name]=str(job.out/name)
 for filename in ['densify_primary_axis.py','mine_outcome_informed_hypotheses.py']:
  job.original_main('beyond',filename,{'ROOT':job.out,'FEATURE_CSV':fp,'RESULTS_CSV':rp})
 for name in ['primary_axis_decile_curve.csv','primary_axis_threshold_sweep.csv','primary_axis_densification.json','outcome_informed_hypotheses.json']:
  job.artifacts[name]=str(job.out/name)
 confirmation(job,'flexible107')

def combined_geometry(job):
 template=read(RUNS/NAMES['geometry']/'spectra_ready_dataset/combined_feature_outcome_table.csv');df=job.refresh(template)
 m=module('geometry','build_combined_and_score_axes.py');df=m.add_common_derived(m.ensure_sequence_features(df),float(job.f['cameo'].seq_len.median()))
 df['hash_fold10']=df.target_id.map(m.stable_fold);df['target_minus_baseline_ca_lddt']=df.ca_lddt-df.baseline_ca_lddt
 job.save('spectra_ready_dataset/combined_feature_outcome_table.csv',df)
 job.original_main('geometry','audit_frozen_reference_topology_axes.py')
 for name in ['frozen_reference_topology_axis_curves.csv','frozen_reference_topology_axes_audit.json']:job.artifacts[name]=str(job.out/name)
 # Full original catalogue, including charge/hydropathy/cys/motif negatives.
 axes=m.axis_catalog();records=[];curves=[]
 for ax in axes:
  for subset,part in [('cameo_discovery',df[(df.dataset=='cameo')&(df.hash_fold10<=5)]),('cameo_confirmation',df[(df.dataset=='cameo')&(df.hash_fold10>=6)]),('external',df[df.dataset=='external_rcsb']),('cameo_scaled',df[df.dataset=='cameo_scaled'])]:
   result=m.score_axis(part,ax['axis_name'],ax['feature'],ax['direction'],subset)
   if isinstance(result,tuple):
    records.append(result[0]);curves.append(result[1])
   else:records.append(result)
 job.save('geometry_candidate_scores.json',records)
 if curves:job.save('geometry_candidate_curves.csv',pd.concat(curves,ignore_index=True))

def acidic_discovery(job):
 # The original discovery was the finite external34 subset (33 finite originally).
 m=module('geometry','build_combined_and_score_axes.py')
 frame=job.joined('external34');frame=frame[frame.ca_lddt.notna()].copy()
 score,curve=m.score_axis(frame,'acidic_window','max_negative_charge_window31','low','original_external_discovery')
 job.save('acidic_discovery_curve.csv',curve);job.save('acidic_discovery_effect.json',score)

def charge_audits(job):
 template=read(RUNS/NAMES['geometry']/'spectra_ready_dataset/combined_feature_outcome_table.csv')
 df=job.refresh(template);job.save('spectra_ready_dataset/combined_feature_outcome_table.csv',df)
 for filename in ['audit_frozen_charge_axis.py','audit_frozen_charge_hydropathy_axis.py']:
  job.original_main('geometry',filename)
 for path in job.out.glob('frozen_*'):
  if path.is_file():job.artifacts[path.name]=str(path)

def evidence(job,expanded=False):
 group='cys' if expanded else 'acid';filename='expanded_all_scored_evidence_table.csv' if expanded else 'combined_evidence_table.csv'
 df=job.refresh(read(RUNS/NAMES[group]/'spectra_ready_dataset'/filename))
 if expanded:
  m=module('cys','expand_all_scored_features.py');df=m.add_expanded_features(df)
  pool=read(RUNS/NAMES['cys']/'spectra_ready_dataset/expanded_candidate_pool_features.csv')
  pool=m.add_expanded_features(pool);m.OUT_POOL=job.out/'recomputed_candidate_pool.csv'
  df=m.add_neighborhood_features(df,pool)
  job.artifacts['recomputed_candidate_pool.csv']=str(m.OUT_POOL)
  screens=[read(RUNS/NAMES[group]/'analysis_outputs/expanded_all_scored_axis_screen.csv')]
 else:
  m=module('acid','ingest_all_evidence_and_screen.py');df=m.normalize_features(df)
  screens=[read(RUNS/NAMES[group]/'analysis_outputs'/n) for n in ['all_evidence_axis_screen.csv','fresh_panel_remaining_axis_screen.csv','post_acidic_axis_screen.csv']]
 screen=pd.concat(screens,ignore_index=True).drop_duplicates(['source','feature','direction'],keep='last');effects=[];curves=[];unusable=[]
 for _,spec in screen.iterrows():
  fn=m.score_axis if expanded else m.score_feature
  value=fn(df,spec.feature,spec.direction,spec.source,int(spec.n_levels))
  if value is None:unusable.append({'source':spec.source,'feature':spec.feature,'direction':spec.direction,'reason':'original function insufficient finite rows/variation'});continue
  effects.append(value)
  sub=df[df.evidence_source.astype(str).eq(str(spec.source))].copy();sub[spec.feature]=pd.to_numeric(sub[spec.feature],errors='coerce');sub=sub[sub.ca_lddt.notna()&sub[spec.feature].notna()]
  levels=m.assign_levels(sub[spec.feature],spec.direction,int(spec.n_levels)) if expanded else m.qlevels(sub[spec.feature],int(spec.n_levels))
  if not expanded and spec.direction=='low':levels=levels.max()-levels
  sub['axis_level']=levels
  c=sub.groupby('axis_level').agg(n=('target_id','size'),ca_lddt_mean=('ca_lddt','mean'),feature_mean=(spec.feature,'mean')).reset_index();c['feature']=spec.feature;c['direction']=spec.direction;c['source']=spec.source;curves.append(c)
 job.save(filename,df);job.save('expanded_screen_effects.json' if expanded else 'all_evidence_screen_effects.json',effects);job.save('screen_unusable.json',unusable)
 job.save('expanded_screen_curves.csv' if expanded else 'all_evidence_screen_curves.csv',pd.concat(curves,ignore_index=True))
 return df

def shared_frames(job):
 """Original constructor, including fresh cross-panel pTM winner selection."""
 if not hasattr(job,'_shared_frames'):
  m=module('shared','analyze_shared_axes.py')
  paths={'cameo_followup_features':('cameo','features.csv'),
         'cameo_followup_results':('cameo','target_model_results.csv'),
         'cameo_scaled_results':('cameo_scaled40','target_model_results.csv'),
         'rcsb_orig_features':('external34','features.csv'),
         'rcsb_orig_results':('external34','target_model_results.csv'),
         'rcsb_exp_features':('flexible107','features.csv'),
         'rcsb_exp_results':('flexible107','target_model_results.csv')}
  m.PATHS={key:job.w/'panels'/panel/file for key,(panel,file) in paths.items()}
  job._shared_frames=m.load_combined_tables()
 return job._shared_frames

def shared(job):
 df,targets,manifest=shared_frames(job);m=module('shared','analyze_shared_axes.py')
 job.save('shared_combined_prospective_performance.csv',df);job.save('shared_target_model_results.csv',targets);job.save('shared_input_manifest.json',manifest)
 # Preserve original tested candidate list, rerun original discovery-direction/confirmation logic.
 features=m.numeric_candidate_features(df);summary,curves,dense=m.score_shared_axes(df,features)
 job.save('shared_candidate_summary.csv',summary);job.save('shared_candidate_curves.csv',curves);job.save('shared_candidate_dense.csv',dense)


def global_axes(job):
 g=module('global','global_hypothesis_audit.py')
 # The archived all-evaluation table defines the tested input/setting inventory,
 # not the answers. Every numerical model output is replaced before deduplication.
 old=read(RUNS/NAMES['global']/'spectra_ready_dataset/all_esmfold2_scored_evaluations.csv')
 previous=job.selected
 try:
  job.selected={name:global_select(r).set_index('target_id') for name,r in job.r.items()}
  d=job.refresh(old)
 finally:job.selected=previous
 d=d.drop(columns=['_ptm_sort','_plddt_sort'],errors='ignore');d=d[d.ca_lddt.notna() & d.sequence_clean.str.len().gt(0)].copy()
 d['sequence_clean']=d.sequence.fillna('').map(g.clean_seq);d['sequence_hash_calc']=d.sequence_clean.map(g.hash_seq)
 d['setting_label']=d.apply(g.setting_label,axis=1);d['budget_score']=d.apply(g.budget_score,axis=1)
 for c in ['ca_lddt','gdt_ts','ca_rmsd']:d['_round_'+c]=pd.to_numeric(d[c],errors='coerce').round(6)
 d=d.drop_duplicates(['target_id','sequence_hash_calc','setting_label','_round_ca_lddt','_round_gdt_ts','_round_ca_rmsd']).drop(columns=['_round_ca_lddt','_round_gdt_ts','_round_ca_rmsd'])
 primary=d.sort_values(['budget_score','setting_label','run_name'],ascending=[False,False,False]).drop_duplicates('sequence_hash_calc')
 for name,frame in [('all_evaluations',d),('primary_sequence',primary)]:
  frame=g.add_features(frame);ef,cv,sl=g.evaluate_hypotheses(frame,name)
  job.save(name+'_features.csv',frame);job.save(name+'_effects.csv',ef);job.save(name+'_curves.csv',cv);job.save(name+'_slices.csv',sl)
 return primary

def proxy(job):
 prior=job.refresh(read(RUNS/NAMES['cys']/'spectra_ready_dataset/expanded_all_scored_evidence_table.csv'))
 combined=job.refresh(read(RUNS/NAMES['cys']/'spectra_ready_dataset/combined_evidence_with_cys_confirmation.csv'))
 fresh=job.joined('cysteine95');fresh['selection']='best_by_ptm'
 p=job.save('proxy_prior.csv',prior);c=job.save('proxy_combined.csv',combined);f=job.save('proxy_fresh.csv',fresh)
 job.original_main('proxy','iterate_proxy_axes.py',{'OUT':job.out,'PRIOR':p,'FRESH':f,'COMBINED':c,'MANIFEST':RUNS/NAMES['cys']/'cys_confirmation_panel_manifest.json'})
 for n in ['candidate_axis_screen.csv','candidate_source_consistency.csv','candidate_control_models.csv']:job.artifacts[n]=str(job.out/n)

def run_axis(axis,workspace):
 job=Analysis(axis,workspace)
 if job.axis in [1,2]:cameo(job)
 elif job.axis==3:flexible(job)
 elif job.axis==4:confirmation(job,'charge97');shared(job);charge_audits(job)
 elif job.axis==5:confirmation(job,'acidic78');acidic_discovery(job);evidence(job)
 elif job.axis==6:confirmation(job,'cysteine95');evidence(job,True)
 elif job.axis in [7,8]:global_axes(job);proxy(job) if job.axis==8 else None
 elif job.axis==9:combined_geometry(job)
 elif job.axis==10:confirmation(job,'viral36')
 elif job.axis in [11,12]:
  confirmation(job,'envelope38')
  job.original_main('envelope','discover_envelope_subaxes.py',{'TARGET_LEVEL':job.out/'envelope38_target_level.csv','OUT_CANDIDATES':job.out/'envelope_subaxis_candidates.csv','OUT_FEATURED':job.out/'envelope_subaxis_features.csv','OUT_REPORT':job.out/'envelope_subaxis_report.md'})
  job.artifacts['envelope_subaxis_candidates.csv']=str(job.out/'envelope_subaxis_candidates.csv')
  if job.axis==12:confirmation(job,'surface45')
 else:raise ValueError('Unknown axis '+str(axis))
 report={'axis':job.axis,'status':'analysis_complete','inputs':job.checks,'artifacts':job.artifacts,'historical_decisions':'Unchanged in original notebooks; these are new numerical analyses. Any fixed historical prose emitted by original programs is diagnostic and is not a new agent determination.','mode':json.loads((job.w/'feature_reconstruction_report.json').read_text())['mode']}
 dump(job.out/'WORKFLOW_REPORT.json',report);return report
