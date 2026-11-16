import pathlib,json,io,ast,re,hashlib
import pandas as pd,numpy as np
from scipy.stats import spearmanr,norm
R=pathlib.Path(__file__).resolve().parents[2]; root=R/'reproduction/inline/conch'
results=[]
def tables(n):
 out=[]
 for ci,c in enumerate(n['cells']):
  for oi,o in enumerate(c.get('outputs',[])):
   html=''.join(o.get('data',{}).get('text/html',[]))
   if '<table' in html:
    frames=pd.read_html(io.StringIO(html))
    if not frames:continue
    d=frames[0]
    if isinstance(d.columns,pd.MultiIndex):
     d.columns=[next((str(x) for x in reversed(col) if not str(x).startswith('Unnamed')),str(col)) for col in d.columns]
    out.append((ci,oi,d))
 return out
for p in sorted(root.glob('*/*.ipynb')):
 n=json.loads(p.read_text());fam=p.parent.name;t=int(p.stem[-2:]);tt=tables(n);checks=[]
 def add(label,value,evidence):checks.append(dict(check=label,value=value,evidence=evidence))
 for ci,c in enumerate(n['cells']):
  if c['cell_type']=='code':ast.parse(''.join(c['source']))
 add('Code syntax and saved-output errors',{'code_cells':sum(c['cell_type']=='code' for c in n['cells']),'errors':sum(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[]))},'All code cells parsed; all saved output objects inspected.')
 assert checks[-1]['value']['errors']==0
 if fam=='conch-primary':
  for col in ['balanced_accuracy','mean_class_adjusted_correct_residual','stable_class_macro_recall']:
   d=next(d for ci,oi,d in tt if 'level' in d and col in d)
   add('Spearman '+col,float(spearmanr(d.level,d[col]).statistic),'Recomputed from saved six-level table, independently of notebook decision code.')
  if t==4:
   panels=[d for ci,oi,d in tt if 'tum_recall' in d];conf,exp=panels
   counts=np.rint(exp.tum_recall.to_numpy()*exp.n.to_numpy()).astype(int)
   low=counts[:7].sum()/exp.n.iloc[:7].sum();high=counts[7:].sum()/exp.n.iloc[7:].sum();diff=low-high
   se=np.sqrt(low*(1-low)/2800+high*(1-high)/1200);ci=[float(diff-1.96*se),float(diff+1.96*se)]
   assert abs(diff-.24952380952380948)<1e-12
   add('Tumor main contrast and normal interval',dict(low_group_successes=int(counts[:7].sum()),high_group_successes=int(counts[7:].sum()),difference=diff,ci95=ci),'Rounded saved recall × sample count recovers exact integer successes; recomputed pooled levels1–7 versus8–10.')
   add('Tumor confirmation correlation',float(spearmanr(conf.level,conf.tum_recall).statistic),'Saved six-level tumor table.')
 if fam in ['conch-gpt-r1','conch-gpt-r2']:
  effects=[d for ci,oi,d in tt if {'cohort','method','drop','classes'}.issubset(d.columns)]
  within=[d for ci,oi,d in tt if 'label' in d and {'1','5'}.issubset(d.columns) and len(d)<=20]
  if effects:
   # Last qualifying table is the per-class recall pivot, not the earlier integer count table.
   w=within[-1];ef=effects[0]
   for co,g in w.groupby('cohort'):
    common=g[['1','5']].dropna();drop=float((common['1']-common['5']).mean());reported=float(ef[(ef.cohort==co)&(ef.method=='CONCH')]['drop'].iloc[0]);assert abs(drop-reported)<2e-6
    add(co+' common-class endpoint contrast',dict(recomputed=drop,reported=reported,classes=len(common)),'Saved within-class recall pivot, common nonmissing endpoints.')
   adj=next(d for ci,oi,d in tt if 'odds_ratio'in d and 'beta'in d)
   assert np.max(np.abs(np.exp(adj.beta)-adj.odds_ratio))<2e-6
   add('Adjusted coefficient/odds-ratio arithmetic',float(np.max(np.abs(np.exp(adj.beta)-adj.odds_ratio))),'exp(beta) compared with displayed odds ratio for all fitted terms; display rounding tolerance2e-6.')
   if fam=='conch-gpt-r2':
    crc=w[w.cohort=='CRC'];means=crc[['1','2','3','4','5']].mean();add('CRC plotted versus endpoint class populations',dict(classes=crc[['1','2','3','4','5']].notna().sum().tolist(),plotted_drop=float(means.iloc[0]-means.iloc[-1])),'Available-class means independently recomputed; endpoint contrast uses common7 above.')
  elif fam=='conch-gpt-r1':
   cnt=next(d for ci,oi,d in tt if 'label'in d and {'1','5'}.issubset(d.columns));selected={str(co):g.loc[g[['1','2','3','4','5']].min(axis=1)>=50,'label'].tolist() for co,g in cnt.groupby('cohort')}
   add('Eligibility count rule',selected,'Recomputed >=50 perclass in every level directly from saved counts. No prediction performance checked because none is claimed.')
  else:
   d=next(d for ci,oi,d in tt if 'explicit_mpp_records'in d);assert d.explicit_mpp_records.sum()==0;add('Magnification metadata availability',d[['cohort','images','explicit_mpp_records']].to_dict('records'),'Saved image metadata screen; this is not a model-performance test.')
 if fam=='conch-opus-r1':
  fitted=[d for ci,oi,d in tt if {'coefficient','odds_ratio'}.issubset(d.columns)]
  err=max(float(np.max(np.abs(np.exp(d.coefficient)-d.odds_ratio))) for d in fitted);assert err<1e-4
  add('Logistic coefficients to odds ratios',err,'Full and internal split coefficient tables; maxrounding difference.')
 if fam=='conch-opus-r2':
  d=next(d for ci,oi,d in tt if 'conch_acc'in d);d=d.sort_values('sigma');a=np.rint(d.conch_acc*1080).astype(int);b=np.rint(d.baseline_acc*1080).astype(int)
  target=float((a.iloc[0]-a.iloc[-1])/1080);baseline=float((b.iloc[0]-b.iloc[-1])/1080)
  assert abs(target-.537962962962963)<1e-12
  add('Paired-blur point estimates',dict(target_drop=target,baseline_drop=baseline,difference_in_differences=target-baseline,n=1080,conch_correct=a.tolist(),reference_correct=b.tolist()),'Integer correct counts recovered from rounded saved accuracy ×1080; independent arithmetic. Bootstrap interval not reexecuted.')
 if fam in ['conch-kimi-r1','conch-kimi-r2']:
  curve=next(d for ci,oi,d in tt if {'cohort','method','balanced_accuracy','level'}.issubset(d.columns));effects=[d for ci,oi,d in tt if {'cohort','method','drop'}.issubset(d.columns)]
  if effects:
   e=effects[0];diffs=[]
   for (co,m),g in curve.groupby(['cohort','method']):
    g=g.sort_values('level');drop=float(g.balanced_accuracy.iloc[0]-g.balanced_accuracy.iloc[-1]);reported=float(e[(e.cohort==co)&(e.method==m)]['drop'].iloc[0]);assert abs(drop-reported)<2e-6;diffs.append(dict(cohort=co,method=m,recomputed=drop,reported=reported))
   add('All method/panel endpoint drops',diffs,'Independently subtracted saved curve endpoints; error<2e-6 from six-decimal printing.')
  else:add('Native cohort comparison scope',dict(levels=curve.level.unique().tolist(),panels=curve.cohort.unique().tolist()),'One native level; no degradation effect table expected.')
  within=next(d for ci,oi,d in tt if 'label'in d and 'method'in d)
  cmp=[]
  for (co,m),g in within.groupby(['cohort','method']):
   for col in g.columns[3:]:
    lev=float(col);reported=float(curve[(curve.cohort==co)&(curve.method==m)&(curve.level==lev)].balanced_accuracy.iloc[0]);value=float(g[col].mean());assert abs(value-reported)<2e-6
    cmp.append(abs(value-reported))
  add('Balanced accuracy from class recalls',dict(comparisons=len(cmp),max_absolute_error=max(cmp)),'Arithmetic mean of all nine saved per-class recalls at every method/panel/level.')
 results.append(dict(id=f'{fam}-{p.stem}',notebook=str(p.relative_to(R)),checks=checks))
pathlib.Path(__file__).with_name('conch-numerical-checks.json').write_text(json.dumps(results,indent=2)+'\n')
print('Checked',len(results),'entries;',sum(len(x['checks']) for x in results),'check groups; no fresh inference.')
