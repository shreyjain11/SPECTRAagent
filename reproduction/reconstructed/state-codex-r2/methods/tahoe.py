"""Reconstruct Codex-r2 A8/A9/A10/A10R using released scores and public inputs."""
import argparse,ast,json,tomllib
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from scipy.stats import spearmanr
from common import checked,dump,sha,save_receipt,cluster_fit,curve,fisher

CELLS={'C32':'C32','HOP62':'HOP62','HepG2/C3A':'HepG2-C3A','Hs 766T':'Hs 766T','PANC-1':'PANC-1'}
def parse(s):
    a=ast.literal_eval(s)
    if len(a)!=1 or len(a[0])!=3:raise ValueError(f'Unexpected condition {s}')
    drug,dose,unit=a[0]
    return str(drug).strip(),float(dose),str(unit)
def cohort(root):
    p=checked(root,'metadata/generalization.toml');t=tomllib.loads(p.read_text());sets=[]
    for c in CELLS:sets.append({parse(x) for x in t['fewshot'][f'tahoe_holdout.{c}']['test']})
    common=set.intersection(*sets);drugs=sorted({x[0] for x in common if all((x[0],v,'uM') in common for v in [.05,.5,5.])})
    d=pd.DataFrame([(c,g,v,'uM') for c in CELLS for g in drugs for v in [.05,.5,5.]],columns=['context','drug','dose','unit'])
    d['weakness']=-np.log10(d.dose);d['dose_level']=d.dose.map({5.:1,.5:2,.05:3})
    out=root/'computed/tahoe';out.mkdir(parents=True,exist_ok=True);d.to_csv(out/'cohort.csv',index=False)
    dump(out/'cohort_summary.json',dict(drugs=len(drugs),conditions=len(drugs)*3,units=len(d),test_list_counts=dict(zip(CELLS,map(len,sets))),eligibility='intersection of five official test lists; complete fixed three-dose triplet per exact stripped drug name'))
    contract=json.loads((root/'originals/supporting/audit/axis/frozen_axis_A7_dose_official.json').read_text())
    dump(out/'A7_contract_diagnostic.json',dict(direction=contract['direction'],written_success_criterion=contract['success_criteria'],low_minus_high_weakness=float(-np.log10(.05)+np.log10(5.)),direction_implies_slope='negative',written_criterion_requires_slope='positive',sign_contradiction=('above zero' in contract['success_criteria'] and 'lower administered dose predicts lower' in contract['direction']),outcome_analysis_performed=False,original_decision='Retired after schema/initial-row inspection because the written sign criterion contradicted the directional hypothesis.'))
    return d,[p,root/'originals/supporting/audit/axis/frozen_axis_A7_dose_official.json']
def controls(root):
    p=checked(root,'metadata/tahoe_obs_metadata.parquet');out=root/'computed/tahoe';out.mkdir(parents=True,exist_ok=True)
    data=ds.dataset(p,format='parquet');cols=['cell_name','drugname_drugconc','plate','pcnt_mito','gene_count','tscp_count','pass_filter']
    d=data.to_table(columns=cols,filter=ds.field('cell_name').isin(list(CELLS))).to_pandas()
    for c in ['cell_name','drugname_drugconc','plate']:d[c]=d[c].astype(str)
    mapping={x:parse(x) for x in d.drugname_drugconc.unique()};d['drug']=d.drugname_drugconc.map(lambda x:mapping[x][0]);d['dose']=d.drugname_drugconc.map(lambda x:mapping[x][1])
    d=d.rename(columns={'cell_name':'context'})
    g=d.groupby(['context','drug','dose'],observed=True).agg(n_treated=('drug','size'),mito=('pcnt_mito','mean'),gene_mean=('gene_count','mean'),umi_mean=('tscp_count','mean')).reset_index()
    cb=d[d.drug=='DMSO_TF'].groupby(['context','plate'],observed=True).size()
    unique_plates=d[['context','drug','dose','plate']].drop_duplicates()
    unique_plates['n_control_plate']=[cb.get((c,p),0) for c,p in zip(unique_plates.context,unique_plates.plate)]
    cnt=unique_plates.groupby(['context','drug','dose'],observed=True).n_control_plate.sum().rename('n_control').reset_index()
    g=g.merge(cnt,on=['context','drug','dose'],validate='one_to_one');g.to_csv(out/'condition_controls.csv',index=False)
    save_receipt(root,'tahoe_controls',[p],[out/'condition_controls.csv'],dict(rows=len(d),conditions=len(g),control_matching='unique observed technical plates for each condition; each DMSO cell counted once per condition'),['Original count helper absent; all public metadata cells are aggregated and control counts are matched by observed technical plates. This choice is explicit and tested against historical adjusted results, never tuned to them.'])
    return g
def scores(root,model,setting):
    rows=[];sources=[]
    for c,stem in CELLS.items():
        p=checked(root,f'{model}/{setting}/{stem}_results.csv');sources.append(p);d=pd.read_csv(p)
        parsed=d.perturbation.map(parse);d['drug']=parsed.map(lambda x:x[0]);d['dose']=parsed.map(lambda x:x[1]);d['context']=c
        d=d[['context','drug','dose','de_spearman_lfc_sig','de_nsig_counts_real']].rename(columns={'de_spearman_lfc_sig':'score','de_nsig_counts_real':'n_de'})
        if d.duplicated(['context','drug','dose']).any():raise ValueError('Duplicate normalized condition')
        rows.append(d)
    return pd.concat(rows,ignore_index=True),sources
def reference(root,co):
    rows=[];sources=[]
    for c,stem in CELLS.items():
        p=checked(root,f'ST-HVG-Tahoe/zeroshot/state_generalization_zeroshot_X_hvg/eval_best.ckpt/{stem}_real_de.csv');sources.append(p)
        d=pd.read_csv(p,usecols=['target','feature','reference_mean','fold_change','fdr'])
        keep={(r.drug,r.dose) for r in co[co.context==c].itertuples()}
        for target,g in d.groupby('target',sort=True):
            drug,dose,_=parse(target)
            if (drug,dose) not in keep:continue
            g=g[(g.fdr<.05)&np.isfinite(g.reference_mean)&np.isfinite(g.fold_change)&(g.fold_change>0)]
            value=float(spearmanr(-np.log1p(g.reference_mean),np.log2(g.fold_change)).statistic) if len(g)>=20 else np.nan
            rows.append(dict(context=c,drug=drug,dose=dose,reference_score=value,n_reference_features=len(g)))
    d=pd.DataFrame(rows);d.to_csv(root/'computed/tahoe/basal_reference_scores.csv',index=False);return d,sources
def run(root,draws=10000):
    out=root/'computed/tahoe';co,sources=cohort(root);ctrl=controls(root);sources.append(root/'inputs/metadata/tahoe_obs_metadata.parquet')
    results={};all_outputs=[out/'cohort.csv',out/'cohort_summary.json',out/'A7_contract_diagnostic.json',out/'condition_controls.csv']
    stages=[('A8','ST-SE-Tahoe','fewshot/state_generalization_X_state/eval_best.ckpt'),('A10','ST-HVG-Tahoe','zeroshot/state_generalization_zeroshot_X_hvg/eval_best.ckpt'),('A9','ST-SE-Tahoe','zeroshot/state_generalization_zeroshot_X_state/eval_best.ckpt')]
    for name,model,setting in stages:
        print('TAHOE',name,flush=True);s,ps=scores(root,model,setting);sources+=ps
        d=co.merge(s,on=['context','drug','dose'],validate='one_to_one',how='left').merge(ctrl,on=['context','drug','dose'],how='left',validate='one_to_one')
        missing=d[~np.isfinite(d.score)].copy();missing.to_csv(out/f'{name}_excluded_scores.csv',index=False);d=d[np.isfinite(d.score)].copy();d['zscore']=fisher(d.score)
        for v in ['n_de','n_treated','n_control','gene_mean','umi_mean']:d['log_'+v]=np.log1p(d[v])
        axis='mito' if name=='A9' else 'weakness';adjust=['log_n_de','log_n_treated','log_n_control'];fixed=['context']
        if name=='A9':
            d=d.dropna(subset=['mito',*adjust,'log_gene_mean','log_umi_mean']);adjust+=['log_gene_mean','log_umi_mean'];fixed+=['dose']
            order=d.sort_values(['mito','context','drug','dose'],kind='mergesort').index
            d.loc[order,'mito_level']=np.floor(np.arange(len(d))*5/len(d)).astype(int)+1;level='mito_level'
        else:level='dose_level'
        raw,boot=cluster_fit(d,'zscore',axis,'drug',fixed=[] if name=='A9' else ['context'],cluster_fixed=True,draws=draws,seed=20260716)
        adjusted,badj=cluster_fit(d,'zscore',axis,'drug',adjust=adjust,fixed=fixed,cluster_fixed=True,draws=draws,seed=20260716)
        cv,cb=curve(d,level,'score','drug',draws,20260716);cv.to_csv(out/f'{name}_curve.csv',index=False)
        ep=cb[str(cv.level.iloc[-1])]-cb[str(cv.level.iloc[0])]
        result=dict(raw=raw,adjusted=adjusted,curve=cv.to_dict('records'),endpoint=float(cv['mean'].iloc[-1]-cv['mean'].iloc[0]),endpoint_ci95=np.quantile(ep,[.025,.975]).tolist(),score_exclusions=len(missing),recomputed_negative_degradation=bool(raw['ci95'][1]<0 and adjusted['coefficient']<0))
        if name=='A10':
            ref,ps=reference(root,co);sources+=ps;d=d.merge(ref,on=['context','drug','dose'],validate='one_to_one');pair=d.dropna(subset=['reference_score']).copy();pair['reference_z']=fisher(pair.reference_score)
            rf,rb=cluster_fit(pair,'reference_z','weakness','drug',fixed=['context'],cluster_fixed=True,draws=draws,seed=20260716)
            sf,sb=cluster_fit(pair,'zscore','weakness','drug',fixed=['context'],cluster_fixed=True,draws=draws,seed=20260716)
            delta=sf['coefficient']-rf['coefficient'];result['same_example_reference']=dict(reference=rf,state=sf,difference=delta,difference_ci95=np.quantile(sb-rb,[.025,.975]).tolist(),historical_rule_classification='larger' if delta<-.02 else 'smaller' if delta>.02 else 'comparable')
            all_outputs.append(out/'basal_reference_scores.csv')
        d.to_csv(out/f'{name}_units.csv',index=False);results[name]=result;dump(out/f'{name}_summary.json',result)
        all_outputs += [out/f'{name}_curve.csv',out/f'{name}_units.csv',out/f'{name}_summary.json',out/f'{name}_excluded_scores.csv']
    # Historical values are loaded only AFTER all source-level calculations.
    comparisons=[]
    for name,fn in [('A8','A8_tahoe_dose_summary.json'),('A10','A10_dose_hvg_summary.json'),('A9','A9_mito_summary.json')]:
        historical_path=root/'originals/supporting/audit/results'/fn;sources.append(historical_path)
        old=json.loads(historical_path.read_text());key='mito_slope' if name=='A9' else 'weakness_slope_fisher_z_per_sd'
        historical=old.get(key);new=results[name]['raw']['coefficient'];comparisons.append(dict(analysis=name,metric='raw_slope',historical=historical,reconstructed=new,difference=None if historical is None else new-historical))
    dump(out/'historical_comparison.json',comparisons);all_outputs.append(out/'historical_comparison.json')
    save_receipt(root,'tahoe_analysis',sorted(set(sources)),all_outputs,dict(analyses=list(results),cohort_drugs=co.drug.nunique(),cohort_units=len(co)),['Original executable analysis helpers absent; implementations follow frozen contracts.','Population-SD normalization over complete analyzed rows; unknown original dose-bootstrap seed is explicitly fixed at 20260716, 10000 draws.','Original count helper absent; metadata and technical-plate matching are documented in tahoe_controls_receipt.json.','The A7 written-sign contradiction is checked directly against its frozen contract; no A7 outcome analysis is invented.'])
    return results
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--draws',type=int,default=10000);a=p.parse_args();run(a.root.resolve(),a.draws)
