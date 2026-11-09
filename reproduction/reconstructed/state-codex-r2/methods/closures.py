"""Recompute eligibility/assignment diagnostics without inventing unperformed tests."""
import argparse,json
from pathlib import Path
import numpy as np
import pandas as pd
from common import dump,save_receipt

def run(root):
    out=root/'computed/closures';out.mkdir(parents=True,exist_ok=True)
    co=pd.read_csv(root/'computed/tahoe/cohort.csv');counts=pd.read_csv(root/'computed/tahoe/condition_controls.csv')
    d=co.merge(counts,on=['context','drug','dose'],validate='one_to_one',how='left');d['sampling_weakness']=-np.log1p(d.n_treated)
    order=d.dropna(subset=['sampling_weakness']).sort_values(['sampling_weakness','context','drug','dose'],kind='mergesort').index
    d.loc[order,'support_level']=np.floor(np.arange(len(order))*5/len(order)).astype(int)+1
    d.to_csv(out/'secondary_input_axes.csv',index=False)
    support=d.groupby('support_level').agg(units=('drug','size'),mean_treated=('n_treated','mean'),min_treated=('n_treated','min'),max_treated=('n_treated','max')).reset_index();support.to_csv(out/'support_levels.csv',index=False)
    records=json.loads((root/'methods/sources.json').read_text())['inputs'];inv=[]
    for r in records:
        if not r['path'].startswith('ST-') or not r['path'].endswith('_results.csv'):continue
        model,path=r['path'].split('/',1);dataset='Replogle' if 'Replogle' in model else 'Tahoe';modality='genetic CRISPRi' if dataset=='Replogle' else 'chemical drug'
        inv.append(dict(dataset=dataset,modality=modality,model=model,representation='SE' if '-SE-' in model else 'HVG',setting=path.split('/')[0],context=Path(path).name.removesuffix('_results.csv'),source_path=r['path'],source_sha256=r['sha256']))
    inv=pd.DataFrame(inv);inv.to_csv(out/'release_modality_assignments.csv',index=False)
    # Explicit algebraic identification check: modality is exactly the dataset
    # dummy. No prediction outcome or regression response is needed.
    dataset=(inv.dataset=='Tahoe').astype(float).values;modality=(inv.modality=='chemical drug').astype(float).values
    X=np.column_stack([np.ones(len(inv)),dataset,modality]);rank=int(np.linalg.matrix_rank(X));assert np.array_equal(dataset,modality)
    historical=json.loads((root/'originals/supporting/audit/results/tahoe_prospective_summary.json').read_text())
    manifest=json.loads((root/'originals/supporting/audit/data/prospective/tahoe_pseudobulk_parquet_manifest.json').read_text())
    summary=pd.DataFrame(manifest['parquet_files']).groupby('config').agg(shards=('filename','size'),bytes=('size','sum')).reset_index();summary.to_csv(out/'original_public_shard_inventory.csv',index=False)
    status=dict(A2e=dict(original_status='Unscored; original prospective pseudobulk reconciliation did not finish',reconstructed_cohort_drugs=int(co.drug.nunique()),reconstructed_cohort_units=len(co),current_work='Original cohort and source inventory reconstructed; original partial block map was not included in surviving handoff, so1536-block reconciliation is historical-only.',historical_retained_summary=historical,original_879_gene_mapping_status='Original mapping hash/definition survives; mapping rows were not included in this handoff. No879-gene outcome analysis was originally completed.'),A3=dict(original_status='Unscored dependency closure',reconstructed_input_level_counts=support.to_dict('records'),outcome_test_performed=False),A5=dict(original_status='Unscored A2e-dependent dose test; distinct from completed A10',reconstructed_dose_levels=sorted(co.dose.unique().tolist()),outcome_test_performed=False),A6=dict(original_status='Unscored A2e-dependent family interaction',release_assignment_rows=len(inv),outcome_test_performed=False),A4=dict(original_status='Nonidentifiable modality contrast',design_columns=['intercept','Tahoe dataset','chemical modality'],design_rank=rank,number_columns=3,exact_modality_dataset_collinearity=True,outcome_test_performed=False))
    dump(out/'closure_diagnostics.json',status)
    sources=[root/'computed/tahoe/cohort.csv',root/'computed/tahoe/condition_controls.csv',root/'methods/sources.json',root/'originals/supporting/audit/data/prospective/tahoe_pseudobulk_parquet_manifest.json',root/'originals/supporting/audit/axis/frozen_axis_secondary.json',root/'originals/supporting/audit/results/tahoe_prospective_summary.json']
    save_receipt(root,'closures',sources,list(out.glob('*.csv'))+[out/'closure_diagnostics.json'],dict(support_units=len(d),release_rows=len(inv),modality_design_rank=rank),['The original unfinished aggregation is not silently completed as a new biological analysis.','Secondary axis input values are regenerated from actual metadata; no original secondary performance curve existed.','The1536-block partial reconciliation and879-gene mapping rows did not survive this handoff; their counts/hash are retained historical evidence, not newly recomputed claims.'])
    return status
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root.resolve())
