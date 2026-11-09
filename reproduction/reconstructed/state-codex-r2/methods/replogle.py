"""Source-level basal distance, released LFC scoring, and magnitude eligibility.

Reconstructed from original frozen contracts, not from desired output values.
"""
import argparse,itertools,json,re,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import rankdata,spearmanr,pearsonr
from common import checked,dump,sha,save_receipt,cluster_fit,curve,fisher,zscore
CTX=['k562','jurkat','hepg2','rpe1']

def axes(root):
    out=root/'computed/replogle';out.mkdir(parents=True,exist_ok=True)
    ep=checked(root,'metadata/depmap_24q4_protein_coding_tpm_logp1.csv');hp=checked(root,'metadata/hpa_rna_celline.tsv.zip');mp=checked(root,'metadata/depmap_24q4_model.csv')
    ids={'k562':['ACH-000551'],'jurkat':['ACH-000995'],'hepg2':['ACH-000739'],'rpe1':[f'ACH-00246{i}' for i in range(2,8)]}
    wanted=set(sum(ids.values(),[]));parts=[]
    for chunk in pd.read_csv(ep,index_col=0,chunksize=200):
        part=chunk.loc[chunk.index.intersection(wanted)]
        if len(part):parts.append(part)
    e=pd.concat(parts);e.columns=[re.sub(r'\s+\(.*\)$','',str(x)) for x in e.columns];e=e.T.groupby(level=0,sort=True).mean().T
    if set(e.index)!=wanted:raise ValueError('Original DepMap context map incomplete')
    with zipfile.ZipFile(hp) as z:
        names=[n for n in z.namelist() if n.endswith('.tsv')]
        if len(names)!=1:raise ValueError('Unexpected HPA archive')
        parts=[]
        for h in pd.read_csv(z.open(names[0]),sep='\t',chunksize=500000):
            parts.append(h[h['Cell line'].isin(['K-562','JURKAT','Hep-G2','hTERT-RPE1','Jurkat E6.1'])])
    h=pd.concat(parts);h=h.pivot_table(index='Cell line',columns='Gene name',values='nTPM',aggfunc='mean')
    genes=sorted(set(e.columns)&set(h.columns));pd.Series(genes,name='gene').to_csv(out/'prospective_genes.csv',index=False)
    de=np.stack([e.loc[ids[c],genes].median(axis=0).values for c in CTX]);names=['K-562','JURKAT','Hep-G2','hTERT-RPE1'];ha=np.log2(1+h.loc[names,genes].values);hs=ha.copy();hs[1]=np.log2(1+h.loc['Jurkat E6.1',genes].values)
    def dist(x):
        if not np.isfinite(x).all():raise ValueError('Nonfinite prospective expression')
        return 1-np.corrcoef(rankdata(x,axis=1,method='average'))
    dp,dh,ds=dist(de),dist(ha),dist(hs);rows=[]
    for i,c in enumerate(CTX):
        other=np.arange(4)!=i
        rows.append(dict(context=c,distance=dp[i,other].mean(),nearest_distance=dp[i,other].min(),hpa_distance=dh[i,other].mean(),hpa_e61_distance=ds[i,other].mean()))
    d=pd.DataFrame(rows);d['level']=d.distance.rank(method='first').astype(int);d.to_csv(out/'axis.csv',index=False)
    for n,v in [('depmap',dp),('hpa',dh),('hpa_e61',ds)]:pd.DataFrame(v,index=CTX,columns=CTX).to_csv(out/f'{n}_pairwise.csv')
    summary=dict(genes=len(genes),nearest_unique_values=int(np.unique(np.round(d.nearest_distance,12)).size),panel_mean_unique_values=int(np.unique(np.round(d.distance,12)).size),hpa_rank_correlation=float(spearmanr(d.distance,d.hpa_distance).statistic),hpa_e61_rank_correlation=float(spearmanr(d.distance,d.hpa_e61_distance).statistic),definition='mean of 1−Spearman to other three contexts, per frozen contract; report prose says cosine and conflicts with contract')
    dump(out/'axis_summary.json',summary)
    save_receipt(root,'replogle_axis',[ep,hp,mp],list(out.glob('*pairwise.csv'))+[out/'axis.csv',out/'axis_summary.json',out/'prospective_genes.csv'],summary,['Duplicate DepMap gene symbols and duplicate HPA gene/cell-line rows collapse by arithmetic mean; RPE1 clone expression uses coordinatewise median.'])
    return d

def de_matrix(p):
    d=pd.read_csv(p,usecols=['target','feature','fold_change','fdr']);d=d[d.target!='non-targeting'].copy()
    # Frozen definition is log2 official fold_change. Nonpositive entries are
    # excluded as nonfinite, rather than choosing a result-dependent pseudocount.
    d['lfc']=np.log2(d.fold_change.where(d.fold_change>0));d['significant']=(d.fdr<.05).astype(int)
    q=d.groupby(['target','feature'],sort=True).agg(lfc=('lfc','mean'),significant=('significant','max')).reset_index()
    mat=q.pivot(index='target',columns='feature',values='lfc');nd=q.groupby('target').significant.sum()
    return mat,nd
def row_spearman(a,b):
    out=[]
    for x,y in zip(a,b):
        f=np.isfinite(x)&np.isfinite(y)
        out.append(float(spearmanr(x[f],y[f]).statistic) if f.sum()>=20 else np.nan)
    return np.asarray(out)
def scores(root):
    out=root/'computed/replogle';out.mkdir(parents=True,exist_ok=True);sources=[];mats={};sig={};availability=[]
    for model in ['ST-SE-Replogle','ST-HVG-Replogle']:
        for c in CTX:
            for kind in ['real','pred']:
                p=checked(root,f'{model}/zeroshot/{c}/eval_best.ckpt/{c}_{kind}_de.csv');sources.append(p);print('REPL DE',model,c,kind,flush=True)
                mat,n=de_matrix(p);mats[model,c,kind]=mat;sig[model,c,kind]=n
                availability.extend(dict(model=model,context=c,kind=kind,perturbation=g) for g in mat.index)
    # Official primary source eligibility; representation intersection is an
    # explicit secondary join and cannot change discovery identities silently.
    primary_sets=[set(mats['ST-SE-Replogle',c,k].index) for c in CTX for k in ['real','pred']]
    balanced=set.intersection(*primary_sets);union=set.union(*primary_sets);remaining=union-balanced
    elig=[]
    for p in sorted(union):
        row=dict(perturbation=p,discovery=p in balanced,confirmation_candidate=p in remaining)
        for c in CTX:
            row[c+'_real']=p in mats['ST-SE-Replogle',c,'real'].index;row[c+'_pred']=p in mats['ST-SE-Replogle',c,'pred'].index
        row['confirmation_eligible']=p in remaining and all(row[c+'_'+k] for c in CTX for k in ['real','pred']);elig.append(row)
    pd.DataFrame(elig).to_csv(out/'A2_eligibility.csv',index=False);pd.DataFrame(availability).to_csv(out/'released_condition_availability.csv',index=False)
    genes=sorted(set.intersection(*(set(m.columns) for m in mats.values())),key=str);perts=sorted(balanced);real={c:mats['ST-SE-Replogle',c,'real'].reindex(index=perts,columns=genes).values for c in CTX}
    rows=[]
    for c in CTX:
        truth=real[c];other=[real[x] for x in CTX if x!=c];ref=np.mean(other,axis=0);rms=np.sqrt(np.nanmean(truth**2,axis=1));expected=np.mean([np.sqrt(np.nanmean(x**2,axis=1)) for x in other],axis=0)
        se=row_spearman(truth,mats['ST-SE-Replogle',c,'pred'].reindex(index=perts,columns=genes).values)
        hv=row_spearman(truth,mats['ST-HVG-Replogle',c,'pred'].reindex(index=perts,columns=genes).values);rr=row_spearman(truth,ref)
        for j,p in enumerate(perts):rows.append(dict(context=c,perturbation=p,state_se=se[j],state_hvg=hv[j],reference=rr[j],effect_rms=rms[j],expected_rms=expected[j],n_de=int(sig['ST-SE-Replogle',c,'real'][p]),features=int(np.isfinite(truth[j]).sum())))
    d=pd.DataFrame(rows);valid=d.groupby('perturbation').apply(lambda x:len(x)==4 and np.isfinite(x[['state_se','state_hvg','reference']].values).all(),include_groups=False);d=d[d.perturbation.isin(valid[valid].index)].copy()
    d.to_csv(out/'unit_scores.csv',index=False)
    summary=dict(primary_balanced_perturbations=len(balanced),finite_balanced_perturbations=d.perturbation.nunique(),common_output_features=len(genes),disjoint_candidates=len(remaining),eligible_disjoint_candidates=sum(x['confirmation_eligible'] for x in elig))
    dump(out/'score_summary.json',summary);save_receipt(root,'replogle_scores',sources,[out/'unit_scores.csv',out/'A2_eligibility.csv',out/'released_condition_availability.csv',out/'score_summary.json'],summary,['Nonpositive fold_change is excluded before log2; no pseudocount is invented.','Duplicate output-feature entries collapse by mean log2 fold change.'])
    return d
def analyze(root,draws=10000):
    out=root/'computed/replogle';axis=pd.read_csv(out/'axis.csv');d=pd.read_csv(out/'unit_scores.csv').merge(axis,on='context',validate='many_to_one');counts=pd.read_csv(out/'cell_counts.csv');d=d.merge(counts,on=['context','perturbation'],validate='one_to_one')
    for c in ['effect_rms','n_de','n_treated','n_control']:d['log_'+c]=np.log1p(d[c])
    fits={};cvs=[]
    for metric in ['state_se','state_hvg','reference']:
        d['z_'+metric]=fisher(d[metric]);fit,boot=cluster_fit(d,'z_'+metric,'distance','perturbation',draws=draws,seed=20260715);fits[metric]=fit
        cv,_=curve(d,'level',metric,'perturbation',draws,20260715);cv['metric']=metric;cvs.append(cv)
    # The frozen paired-perturbation contract supports a within-perturbation
    # adjustment as the primary reconstruction. Declare it before comparing
    # historical numbers. Pooled adjustment is a separately labeled sensitivity.
    paired,_=cluster_fit(d,'z_state_se','distance','perturbation',adjust=['log_effect_rms','log_n_de','log_n_treated','log_n_control'],cluster_fixed=True,draws=draws,seed=20260715);fits['adjusted_state_se']=paired
    adj,_=cluster_fit(d,'z_state_se','distance','perturbation',adjust=['log_effect_rms','log_n_de','log_n_treated','log_n_control'],draws=draws,seed=20260715);fits['adjusted_state_se_pooled_sensitivity']=adj
    fits['adjusted_specification_note']='Primary adjustment is a reconstructed perturbation-fixed-effect fit supported by the frozen paired-perturbation contract. Pooled OLS is an additional sensitivity. Numerical agreement with history corroborates but does not prove identity of the absent original helper.'
    # Every context permutation is enumerated, preserving all condition rows.
    context_means=d.groupby('context').z_state_se.mean().reindex(CTX).values;x=axis.set_index('context').loc[CTX,'distance'].values;perm=[]
    for p in itertools.permutations(x):perm.append(float(np.dot(zscore(p),context_means-context_means.mean())/4))
    fits['exact_context_permutation']=dict(n=24,one_sided_p=float(np.mean(np.array(perm)<=fits['state_se']['coefficient']+1e-12)),slopes=perm)
    pd.concat(cvs,ignore_index=True).to_csv(out/'distance_curve.csv',index=False);d.to_csv(out/'distance_units.csv',index=False);dump(out/'distance_summary.json',fits)
    # A2 nomination is recomputed from the same discovery units, with no
    # fabricated confirmation observations when the complete-panel count is zero.
    d['weakness']=-np.log1p(d.expected_rms);d['magnitude_level']=0
    for c,q in d.groupby('context'):
        ix=q.sort_values(['expected_rms','perturbation'],ascending=[False,True],kind='mergesort').index;d.loc[ix,'magnitude_level']=np.floor(np.arange(len(ix))*5/len(ix)).astype(int)+1
    q=d[['expected_rms','weakness','state_se']]-d.groupby('context')[['expected_rms','weakness','state_se']].transform('mean')
    magfit,_=cluster_fit(d,'z_state_se','weakness','perturbation',fixed=['context'],draws=draws,seed=20260715)
    magcv,_=curve(d,'magnitude_level','state_se','perturbation',draws,20260715);magcv.to_csv(out/'magnitude_curve.csv',index=False);d.to_csv(out/'magnitude_units.csv',index=False)
    eligibility=pd.read_csv(out/'A2_eligibility.csv');summary=dict(expected_rms_context_residual_pearson=float(pearsonr(q.expected_rms,q.state_se).statistic),negative_log1p_rms_context_residual_pearson=float(pearsonr(q.weakness,q.state_se).statistic),fit=magfit,disjoint_candidates=int(eligibility.confirmation_candidate.sum()),eligible_confirmation_candidates=int(eligibility.confirmation_eligible.sum()),decision='No original confirmation outcome test: frozen complete-panel eligibility produced no disjoint candidates.')
    dump(out/'magnitude_summary.json',summary)
    old=json.loads((root/'originals/supporting/audit/results/analysis_summary.json').read_text());comparison=[]
    for metric,key in [('state_se','state_se_slope_fisher_z_per_distance_sd'),('state_hvg','state_hvg_slope_fisher_z_per_distance_sd'),('reference','reference_slope_fisher_z_per_distance_sd'),('adjusted_state_se','adjusted_state_distance_coefficient')]:comparison.append(dict(metric=metric,historical=old[key],reconstructed=fits[metric]['coefficient'],difference=fits[metric]['coefficient']-old[key]))
    comparison.append(dict(metric='adjusted_state_se_pooled_sensitivity',historical=old['adjusted_state_distance_coefficient'],reconstructed=adj['coefficient'],difference=adj['coefficient']-old['adjusted_state_distance_coefficient']))
    dump(out/'historical_comparison.json',comparison)
    outputs=[out/x for x in ['distance_curve.csv','distance_units.csv','distance_summary.json','magnitude_curve.csv','magnitude_units.csv','magnitude_summary.json','historical_comparison.json']]
    save_receipt(root,'replogle_analysis',[out/'axis.csv',out/'unit_scores.csv',out/'cell_counts.csv',out/'A2_eligibility.csv',root/'originals/supporting/audit/results/analysis_summary.json'],outputs,dict(perturbations=d.perturbation.nunique(),units=len(d),eligible_disjoint_candidates=summary['eligible_confirmation_candidates']),['Original executable helpers absent; unadjusted OLS and primary perturbation-fixed-effect adjustment follow the signed-LFC and paired-block contract. Pooled adjustment is an explicitly additional sensitivity.','Distance predictor standardized by population SD on all rows; fixed original seed 20260715 and 10000 draws.','A2 within-context equal-count levels use stable descending expected RMS and lexical perturbation ties; reported residual-correlation transform was not fully specified, so raw and negative-log1p versions are both labeled.'])
    return fits,summary
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--stage',choices=['axis','scores','analysis','all'],default='all');ap.add_argument('--draws',type=int,default=10000);a=ap.parse_args();r=a.root.resolve()
    if a.stage in ['axis','all']:axes(r)
    if a.stage in ['scores','all']:scores(r)
    if a.stage in ['analysis','all']:analyze(r,a.draws)
