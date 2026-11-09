"""Documented STATE Codex-r1 transformations, reconstructed 2026-11-09.

No coefficients/results are hardcoded. Original functions are imported unchanged.
S/lineage continuation choices not recovered (seed, axis-z scope) are REQUIRED
caller arguments rather than silently claimed historical settings. See METHODS.md.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

BASE=Path(__file__).resolve().parent
CONTEXTS=['C32','HOP62','HepG2/C3A','Hs 766T','PANC-1']
CONTROLS=['identity_lfc_rmse','log_n_de','log_n_cells']

def original_scoring():
    spec=importlib.util.spec_from_file_location('original_state_scoring',BASE/'original/04_analyze_frozen_axis.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def score_released_outputs(scores_dir, real_dir):
    """Compute the original metrics once per checkpoint, before attaching axes."""
    m=original_scoring();scores_dir=Path(scores_dir);real_dir=Path(real_dir)
    frames=[]
    for cell,stem in m.CONTEXT_FILES.items():
        print(f'Scoring original released DE rows: {scores_dir.name} / {cell}',flush=True)
        custom=m.compute_lfc_scores(real_dir/f'{stem}_real_de.csv',scores_dir/f'{stem}_pred_de.csv')
        released=pd.read_csv(scores_dir/f'{stem}_results.csv').rename(columns={'perturbation':'target'})
        merged=released.merge(custom,on='target',how='inner',validate='one_to_one')
        if len(merged)!=len(released):raise ValueError(f'Released/custom row mismatch: {cell}')
        merged['cell_line']=cell;frames.append(merged)
    return pd.concat(frames,ignore_index=True)

def s_phase_features(obs_path):
    """Native events911/922; full-QC replication from final REPORT64.

    Input is the ORIGINAL Tahoe obs_metadata.parquet (or a hash-recorded exact
    subset preserving these cells), never newly computed cell-cycle scores.
    """
    import pyarrow.dataset as ds
    data=ds.dataset(obs_path,format='parquet')
    filt=ds.field('cell_name').isin(CONTEXTS)&(ds.field('drug')=='DMSO_TF')
    d=data.to_table(columns=['cell_name','plate','S_score','pass_filter'],filter=filt).to_pandas()
    d['cell_name']=d.cell_name.astype(str)
    plate=d.plate.astype(str).str.extract(r'(\d+)')[0]
    if plate.isna().any():raise ValueError('Unknown plate format; do not guess parity')
    d['plate_num']=plate.astype(int)
    rows=[]
    for name,mask in [('all',np.ones(len(d),dtype=bool)),('odd',d.plate_num%2==1),('even',d.plate_num%2==0),('full',d.pass_filter.astype(str).str.lower()=='full')]:
        z=d.loc[mask].groupby('cell_name',observed=True).S_score.agg(['std','count']).reset_index()
        z=z.rename(columns={'cell_name':'cell_line','std':'axis_value','count':'n_baseline_cells'})
        z['subset']=name;z['axis_level']=z.axis_value.rank(method='min').astype(int);rows.append(z)
    return pd.concat(rows,ignore_index=True)

def lineage_features(mapping):
    """Final REPORT90: -log(1+mapped training-context count in lineage).

    mapping is 01_build_prospective_axis.py's full cell_line_mapping.csv,
    based on the original cell map and DepMap23Q4 Model.csv. Counts are not
    inferred from desired endpoint values.
    """
    d=pd.read_csv(mapping) if isinstance(mapping,(str,Path)) else mapping.copy()
    if d.cell_line.duplicated().any():raise ValueError('Duplicate source contexts')
    train=d.loc[~d.cell_line.isin(CONTEXTS)&d.depmap_id.notna()&d.lineage.notna()]
    counts=train.groupby('lineage').cell_line.nunique()
    out=d.loc[d.cell_line.isin(CONTEXTS),['cell_line','lineage']].copy()
    if out.lineage.isna().any():raise ValueError('Held-out context lacks original lineage')
    out['n_training_contexts']=out.lineage.map(counts).fillna(0).astype(int)
    out['axis_value']=-np.log1p(out.n_training_contexts)
    out['axis_level']=out.axis_value.rank(method='dense').astype(int)
    return out

def build_condition_table(scores_dir,real_dir,cell_counts,axis,*,axis_z_scope,scored_rows=None):
    """Original04 score+eligibility joins; explicit continuation z convention.

    scores_dir supplies <context>_pred_de.csv and _results.csv; real_dir
    supplies _real_de.csv. Reuse of HVG observed rows is supported by final
    integrity_checks.json, but callers must verify those hashes beforehand.
    axis requires cell_line, axis_value. Cell counts require target,
    cell_line,n_cells_full,n_cells_all (original.extract_cell_counts).
    """
    m=original_scoring();scores_dir=Path(scores_dir);real_dir=Path(real_dir)
    axis=pd.read_csv(axis) if isinstance(axis,(str,Path)) else axis.copy()
    counts=pd.read_csv(cell_counts) if isinstance(cell_counts,(str,Path)) else cell_counts.copy()
    if scored_rows is None:scored_rows=score_released_outputs(scores_dir,real_dir)
    all_rows=scored_rows.merge(axis,on='cell_line',validate='many_to_one')
    if len(all_rows)!=len(scored_rows):raise ValueError('Axis merge discarded released rows')
    all_rows=all_rows.merge(counts,on=['cell_line','target'],how='left',validate='one_to_one')
    parsed=all_rows.target.map(m.parse_target)
    all_rows['compound_name']=parsed.map(lambda x:x[0]);all_rows['dose']=parsed.map(lambda x:x[1]);all_rows['dose_unit']=parsed.map(lambda x:x[2])
    all_rows['compound']=all_rows.compound_name.map(m.normalize_compound)
    all_rows['partition']=all_rows.compound.map(m.partition_for)
    all_rows['n_cells']=all_rows.n_cells_full.where(all_rows.n_cells_full>0,all_rows.n_cells_all)
    all_rows['log_n_cells']=np.log1p(all_rows.n_cells);all_rows['log_n_de']=np.log1p(all_rows.n_de)
    coverage=all_rows.groupby('target').cell_line.nunique()
    common=all_rows.loc[all_rows.target.isin(coverage[coverage==5].index)].copy()
    eligibility=common.groupby('compound').agg(n_contexts=('cell_line','nunique'),n_doses=('dose','nunique'),n_targets=('target','nunique'),partition=('partition','first'))
    eligible=eligibility.index[(eligibility.n_contexts==5)&(eligibility.n_doses>=2)]
    common=common.loc[common.compound.isin(eligible)].copy()
    if common.n_cells.isna().any():raise ValueError('Missing original condition cell counts')
    populations={'all_rows':all_rows,'eligible_all':common,'confirmation':common.loc[common.partition=='confirmation'],'contexts':axis}
    if axis_z_scope not in populations:raise ValueError('axis_z_scope must explicitly be all_rows, eligible_all, confirmation, or contexts')
    values=populations[axis_z_scope].axis_value
    mu,sd=values.mean(),values.std(ddof=1)
    if not np.isfinite(sd) or sd<=0:raise ValueError('Degenerate axis')
    common['distance_z']=(common.axis_value-mu)/sd
    common.attrs['axis_standardization']={'scope':axis_z_scope,'mean':float(mu),'sample_sd':float(sd)}
    return common,eligibility,all_rows

def bootstrap_slopes_fast(frame,outcome,controls,*,reps,seed,batch_size=512):
    """Same original compound sufficient statistics and multinomial resampling.

    Batched SVD solves reproduce np.linalg.lstsq's default rank threshold;
    batching changes speed, not resampling unit, weighting or random stream.
    """
    m=original_scoring();y,x,names=m.within_design(frame,outcome,controls)
    compounds=frame.compound.to_numpy();unique=np.unique(compounds)
    xtx=np.stack([x[compounds==c].T@x[compounds==c] for c in unique])
    xty=np.stack([x[compounds==c].T@y[compounds==c] for c in unique])
    rng=np.random.default_rng(seed);out=np.empty(reps);idx=names.index('distance_z')
    for start in range(0,reps,batch_size):
        count=min(batch_size,reps-start)
        weights=rng.multinomial(len(unique),np.full(len(unique),1/len(unique)),size=count)
        lhs=np.einsum('bg,gij->bij',weights,xtx,optimize=True)
        rhs=np.einsum('bg,gi->bi',weights,xty,optimize=True)
        # Rank-aware SVD retains the original least-squares behavior if a draw
        # has collinear covariates; a direct solve would fail or amplify noise.
        pinv=np.linalg.pinv(lhs,rcond=np.finfo(float).eps*lhs.shape[-1])
        out[start:start+count]=np.einsum('bij,bj->bi',pinv,rhs)[:,idx]
    return out

def quintile_matching(frame):
    """Original-style quintile indicator adjustment, historically named matching.

    Recovered control_sensitivities.csv explicitly preserves all4020 rows and
    effect_q_1..4/cells_q_1..4, with no continuous controls in this sensitivity.
    The unrecovered cutpoint scope is declared: qcut within the analyzed
    partition, same boundaries across contexts. No rows are matched/dropped.
    """
    m=original_scoring();c=frame.copy()
    c['effect_quintile'],effect_edges=pd.qcut(c.identity_lfc_rmse,5,labels=False,retbins=True,duplicates='drop')
    c['cell_count_quintile'],cell_edges=pd.qcut(c.n_cells,5,labels=False,retbins=True,duplicates='drop')
    controls=[]
    for prefix,column in [('effect_q','effect_quintile'),('cells_q','cell_count_quintile')]:
        for level in range(1,5):
            name=f'{prefix}_{level}';c[name]=(c[column]==level).astype(float);controls.append(name)
    result=m.fit_within(c,'state_lfc_rmse',controls)
    result.update(status='computed',reconstructed_method=True,
        method='Historical matching sensitivity: eight effect/cell-count quintile indicators in original within-target OLS, retaining every analysis row',
        cutpoint_scope='Within the analyzed partition; shared across contexts; inferred because continuation code is absent',
        effect_quintile_edges=effect_edges.tolist(),cell_count_quintile_edges=cell_edges.tolist())
    table=c.groupby(['effect_quintile','cell_count_quintile','cell_line'],observed=True).size().unstack('cell_line',fill_value=0)
    return result,c,table


def analyze_axis(conditions,*,seed,reps,partition='confirmation'):
    """Original within-target OLS; paired compound bootstrap per final REPORT.

    No historical seed is claimed for missing continuation scripts. Retain the
    supplied seed/reps in output. No outcome-dependent choices are made here.
    """
    m=original_scoring();c=conditions.copy() if partition=='all' else conditions.loc[conditions.partition==partition].copy()
    if not np.isfinite(c[['distance_z','state_lfc_rmse',*CONTROLS]].to_numpy()).all():raise ValueError('Nonfinite analysis values')
    out={'reconstruction':True,'seed':seed,'bootstrap_reps':reps,'partition':partition,'axis_standardization':conditions.attrs.get('axis_standardization'), 'models':{}}
    draws={}
    for name,y,cov in [('state_raw','state_lfc_rmse',[]),('state_adjusted','state_lfc_rmse',CONTROLS),('identity_raw','identity_lfc_rmse',[])]:
        fit=m.fit_within(c,y,cov)
        # Same seed => identical compound multiplicities, as required by final report.
        draws[name]=bootstrap_slopes_fast(c,y,cov,reps=reps,seed=seed)
        fit['bootstrap_ci95']=np.quantile(draws[name],[.025,.975]).tolist();out['models'][name]=fit
    diff=draws['state_raw']-draws['identity_raw']
    out['paired_state_minus_identity']={'estimate':out['models']['state_raw']['estimate']-out['models']['identity_raw']['estimate'],'ci95':np.quantile(diff,[.025,.975]).tolist()}
    out['dose_sensitivity']={str(dose):m.fit_within(g,'state_lfc_rmse',CONTROLS) for dose,g in c.groupby('dose')}
    out['leave_one_context_out']={cell:m.fit_within(c[c.cell_line!=cell],'state_lfc_rmse',CONTROLS) for cell in sorted(c.cell_line.unique())}
    # Reuse original compound-balanced context SPC helper. ccle_distance is
    # bookkeeping only here and is never an input to the error calculation.
    c['distance']=c.axis_value;c['ccle_distance']=np.nan
    spc=m.context_spc(c,reps,seed)
    from scipy.stats import spearmanr
    out['context_spearman']=float(spearmanr(spc.distance,spc.state_rmse_mean).statistic)
    out['counts']={'rows':len(c),'targets':int(c.target.nunique()),'compounds':int(c.compound.nunique()),'contexts':int(c.cell_line.nunique())}
    return out,spc
