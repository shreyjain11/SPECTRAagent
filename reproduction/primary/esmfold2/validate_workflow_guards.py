"""Cheap integration checks for fresh-input wiring and explicit missing/stale errors."""
from pathlib import Path
import json,tempfile
import numpy as np
import pandas as pd
import acquisition as a
import original_workflow as w
from validate_original_workflow import stage_retained

checks=[]
with tempfile.TemporaryDirectory(prefix='esm-workflow-guards-') as tmp:
 root=stage_retained(tmp);f=root/'panels/cameo/features.csv';r=root/'panels/cameo/target_model_results.csv'
 before=w.digest(f);commands=a.inference_commands(1,root)
 assert w.digest(f)==before and Path(commands[0]['command'][commands[0]['command'].index('--features')+1]).resolve()==f.resolve()
 checks.append({'check':'inference_command_uses_rebuilt_file_without_restoring_archive','passed':True})
 saved=f.read_bytes();f.write_bytes(saved+b'\n')
 try:w.require_features(1,root)
 except ValueError:checks.append({'check':'changed_feature_hash_rejected','passed':True})
 else:raise AssertionError('Changed features silently accepted')
 f.write_bytes(saved)
 saved_r=r.read_bytes();original=pd.read_csv(r);original.iloc[1:].to_csv(r,index=False)
 try:w.validate_results(1,root)
 except ValueError:checks.append({'check':'missing_expected_target_rejected','passed':True})
 else:raise AssertionError('Incomplete results silently accepted')
 r.write_bytes(saved_r)
 r.rename(r.with_suffix('.hidden'))
 try:w.run_axis(1,root)
 except FileNotFoundError:checks.append({'check':'missing_results_do_not_fall_back_to_archived_measurements','passed':True})
 else:raise AssertionError('Missing results silently accepted')
 r.with_suffix('.hidden').rename(r)
 baseline=w.run_axis(1,root);curve=Path(baseline['artifacts']['spectral_performance_curve.csv']);old=pd.read_csv(curve)
 target=original.iloc[0].target_id;original.loc[original.target_id==target,'ca_lddt']+=0.123;original.to_csv(r,index=False)
 changed=w.run_axis(1,root);new=pd.read_csv(changed['artifacts']['spectral_performance_curve.csv'])
 assert np.max(np.abs(new.target_ca_lddt_mean-old.target_ca_lddt_mean))>0
 checks.append({'check':'changed_model_measurement_changes_generated_curve','passed':True,'target_id':target})
 r.write_bytes(saved_r)
 feature=pd.read_csv(f);feature.loc[feature.target_id==target,'msa_log10_nonquery_rows']+=1.234;feature.to_csv(f,index=False)
 receipt=json.loads((root/'feature_reconstruction_report.json').read_text());receipt['panels']['cameo']['sha256']=w.digest(f);w.dump(root/'feature_reconstruction_report.json',receipt)
 feature_run=w.run_axis(1,root);feature_curve=pd.read_csv(feature_run['artifacts']['spectral_performance_curve.csv'])
 assert not feature_curve.equals(old)
 checks.append({'check':'changed_reconstructed_feature_changes_generated_analysis','passed':True,'target_id':target})
 # A newly higher-confidence prediction must replace an archived cross-panel winner.
 shared_job=w.Analysis(4,root);before=w.shared_frames(shared_job)[0]
 overlap=set(shared_job.f['external34'].target_id)&set(shared_job.f['flexible107'].target_id)
 target=next(t for t in sorted(overlap) if len(before[(before.target_id==t)&(before.source=='RCSB')]))
 p=root/'panels/external34/target_model_results.csv';raw=pd.read_csv(p)
 raw.loc[raw.target_id==target,'ptm']=2.0;raw.loc[raw.target_id==target,'ca_lddt']=0.123;raw.to_csv(p,index=False)
 after=w.shared_frames(w.Analysis(4,root))[0];winner=after[(after.target_id==target)&(after.source=='RCSB')].iloc[0]
 assert winner.result_panel=='original_34' and abs(winner.ca_lddt-0.123)<1e-12
 evidence_job=w.Analysis(5,root);template=pd.read_csv(w.RUNS/w.NAMES['acid']/'spectra_ready_dataset/combined_evidence_table.csv',low_memory=False)
 row=evidence_job.refresh(template[(template.target_id==target)&(template.evidence_source=='RCSB_scaled_combined')]).iloc[0]
 assert row.result_panel=='original_34' and abs(row.ca_lddt-0.123)<1e-12
 checks.append({'check':'new_cross_panel_confidence_winner_propagates_to_combined_screens','passed':True,'target_id':target})
report={'model_inference_executed':False,'downloads_executed':False,'checks':checks,'passed':all(x['passed'] for x in checks)}
w.dump(a.BUNDLE/'WORKFLOW_GUARD_VALIDATION.json',report);print(json.dumps(report,indent=2))
