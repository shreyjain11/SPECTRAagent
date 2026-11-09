"""Explicit retained-data integration checks. Does not download or run any model."""
from pathlib import Path
import json,shutil,sys,time,traceback
import pandas as pd
import acquisition as a
import original_workflow as w

def stage_retained(dest):
 dest=Path(dest);receipt={'mode':'retained_original_data_integration_fixture','panels':{}}
 choices={'cameo':'target_model_results.csv','acidic78':'target_model_results.acidic_window_confirmation.scaled_samples.csv','cysteine95':'target_model_results.cys_confirmation.scaled_samples.csv','viral36':'target_model_results.viral_disulfide_pilot.scaled_samples.csv','envelope38':'target_model_results.envelope_fusion_confirmation.scaled_samples.csv','surface45':'target_model_results.surface_lowhelical_confirmation.scaled_samples.csv'}
 for name,p in a.MANIFEST['panels'].items():
  d=dest/'panels'/name;d.mkdir(parents=True,exist_ok=True)
  f=pd.read_csv(a.BUNDLE/p['source_features'],low_memory=False)
  # All reconstructed CAMEO derivatives are present in the retained original feature fit.
  if name.startswith('cameo'):
   full=pd.read_csv(w.RUNS/w.NAMES['beyond']/'spectra_ready_dataset/prospective_features.followup.csv',low_memory=False)
   f=w.overlay(f,full[full.target_id.isin(f.target_id)])
  f=f.drop(columns=list(w.METRICS),errors='ignore');f.to_csv(d/'features.csv',index=False)
  shutil.copyfile(a.BUNDLE/p['source_run_root']/choices.get(name,'target_model_results.scaled_samples.csv'),d/'target_model_results.csv')
  receipt['panels'][name]={'features':str(d/'features.csv'),'rows':len(f),'sha256':w.digest(d/'features.csv')}
 w.dump(dest/'feature_reconstruction_report.json',receipt)
 return dest

def main():
 dest=Path(sys.argv[1]).resolve();axes=list(map(int,sys.argv[2:])) or list(range(1,13));stage_retained(dest)
 report={'full_raw_to_model_run_executed':False,'inference_executed':False,'downloads_executed':False,'validation_mode':'Explicit retained original input/result fixtures through actual per-axis dispatch','axes':[]}
 for axis in axes:
  start=time.time()
  try:
   result=w.run_axis(axis,dest);entry={'axis':axis,'status':'passed','artifacts':result['artifacts']}
  except Exception as exc:
   entry={'axis':axis,'status':'failed','error':str(exc),'traceback':traceback.format_exc()}
  entry['elapsed_seconds']=round(time.time()-start,3);report['axes'].append(entry);print(json.dumps(entry),flush=True)
  w.dump(a.BUNDLE/'WORKFLOW_VALIDATION.json',report)
if __name__=='__main__':main()
