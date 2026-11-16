"""Apply the fixed statistical helper; execution is a separate recorded step."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
R=HERE.parents[2]
helper=(HERE/'protein_bootstrap.py').read_text()
changes=[]
for axis in range(3,8):
 p=R/f'inline/alphamissense/am-primary/axis-{axis}.ipynb';book=json.loads(p.read_text())
 for i,c in enumerate(book['cells']):
  source=''.join(c['source'])
  if c['cell_type']=='code' and source.startswith('AXIS_NUMBER='):
   old=source
   source=source.replace('MIN_VARIANTS=20;B=5000;rng=np.random.default_rng(42)',helper+'\nMIN_VARIANTS=20;B=5000;rng=np.random.default_rng(42)')
   a=source.index('for (level,score),d in per_assay.groupby')
   b=source.index('curves=pd.DataFrame(rows)',a)
   source=source[:a]+'''for (level,score),d in per_assay.groupby(['level','score']):
    n=d.n.to_numpy(float);values=d.abs_rho.to_numpy()
    interval=protein_cluster_interval(d,'abs_rho','n',rng=np.random.default_rng(42),replicates=B)
    rows.append({'level':level,'score':score,'weighted_abs_rho':np.average(values,weights=n),'mean_abs_rho':values.mean(),'median_abs_rho':np.median(values),**interval,'assays':len(d),'proteins':d.protein.nunique(),'variants':int(n.sum())})
'''+source[b:]
   a=source.index('# Within-assay paired comparisons');b=source.index('contrasts=pd.DataFrame(contrasts)',a)
   source=source[:a]+'''# Preserve the mean assay contrast while resampling whole protein clusters.
contrasts=[]
for score in PREDICTORS:
    d=per_assay[per_assay.score==score];wide=d.pivot(index='assay',columns='level',values='abs_rho')
    assert d.groupby('assay').protein.nunique().max()==1
    protein_for_assay=d.groupby('assay').protein.first()
    for first,last in [(LEVELS[0],LEVELS[-1]),('coarse_hard','coarse_easy')]:
        if first not in wide or last not in wide:continue
        paired=(wide[last]-wide[first]).dropna().rename('difference').to_frame()
        paired['protein']=protein_for_assay.reindex(paired.index)
        if len(paired):
            interval=protein_cluster_interval(paired,'difference',rng=np.random.default_rng(42),replicates=B)
            contrasts.append({'score':score,'first':first,'last':last,'paired_assays':len(paired),'paired_proteins':paired.protein.nunique(),'mean_last_minus_first':paired.difference.mean(),**interval})
'''+source[b:]
   a=source.index('else:\n    for score in PREDICTORS:',source.index('fig,ax=plt.subplots'))
   b=source.index("ax.set(xticks=",a)
   source=source[:a]+'''else:
    unavailable=False
    for score in PREDICTORS:
        d=curves[curves.score==score].set_index('level').reindex(LEVELS)
        y=d.weighted_abs_rho.to_numpy();x=np.arange(len(LEVELS));valid=np.isfinite(d.ci_low)&np.isfinite(d.ci_high)
        line,=ax.plot(x,y,marker='o',label=score)
        ax.errorbar(x[valid],y[valid],yerr=np.maximum(0,np.array([y[valid]-d.ci_low[valid],d.ci_high[valid]-y[valid]])),fmt='none',capsize=3,color=line.get_color())
        if (~valid).any():
            unavailable=True
            ax.scatter(x[~valid],y[~valid],facecolors='white',edgecolors=line.get_color(),s=55,zorder=5)
    ax.set(ylabel='Variant-weighted mean |Spearman correlation|');ax.legend()
    if unavailable:
        fig.text(.5,-.06,'Open points: interval unavailable; independent protein counts are listed in the table.',ha='center',fontsize=9)
'''+source[b:]
   assert source!=old;c['source']=source.splitlines(True);changes.append(dict(axis=axis,cell=i,kind='protein_cluster_uncertainty_and_plot'))
  elif c['cell_type']=='code' and source.startswith('selected=contrasts['):
   old=source
   source=source.replace("if x.ci_low>0:decision='Retain a directional association: predictive agreement is greater in the final level within the same assays. The displayed references, assay-family composition, residue concentration and DMS-spread controls constrain the interpretation.'",'''if not np.isfinite(x.ci_low) or not np.isfinite(x.ci_high):
        decision=f"The fixed endpoint contains {int(x.paired_assays)} paired assay(s) from {int(x.paired_proteins)} protein(s); descriptive difference={x.mean_last_minus_first:.6f}. Between-protein uncertainty is unavailable ({x.ci_status}). Insufficient independent replication to establish a general directional association."
    elif x.ci_low>0:decision=f"The fixed endpoint difference is positive in this cohort ({int(x.paired_assays)} paired assays; {int(x.paired_proteins)} proteins), with a protein-cluster interval excluding zero. This is a conditional association, not evidence that every AutoSPECTRA requirement is met. References, protein coverage, residue concentration and DMS-spread controls limit the interpretation."''')
   source=source.replace("'bootstrap_unit':'assay'","'bootstrap_unit':'protein cluster (all assays retained together)'" )
   assert source!=old;c['source']=source.splitlines(True);changes.append(dict(axis=axis,cell=i,kind='replication_aware_decision_and_receipt'))
  elif c['cell_type']=='markdown':
   old=source
   if i==0:
    source=source.replace('Use the fixed 73-assay','The full acquisition workflow below uses the fixed 73-assay')
    source+='\n**Statistical recalculation, November 15:** Sections 5–6 below were rerun from the public retained DMS members, official-score subset and recorded alignment arrays, with the same panel, coordinate filters and levels. Earlier acquisition/alignment outputs retain their original execution. This recalculation did not rerun model inference or fresh MMseqs clustering. [Inputs, commands and before/after evidence](../../../corrections/scientific_20261115/alphamissense/README.md).\n'
    if axis==6:source+='\nThe recorded-profile route changes the largest displayed PSSM weighted curve value by about 0.0000073 relative to the previous fresh-profile calculation. This small reference difference is recorded separately from the uncertainty correction; AlphaMissense/BLOSUM points and sample counts are unchanged at displayed precision.\n'
   if source.startswith('## 5.'):
    source='''## 5. Curves and controls

Require at least 20 variants per assay/level. Calculate signed and absolute Spearman correlations; absolute values describe agreement strength and discard direction. Curve means remain variant-count weighted, and paired endpoint estimates remain means of within-assay differences.

Uncertainty now resamples proteins 5,000 times, keeping repeated assays from each protein together. Both assay and protein counts are shown. An interval is unavailable with fewer than two proteins or no empirical resampling variation; two proteins is only a mechanical minimum, not adequate population coverage. Family summaries, residue concentration, terminal positions and DMS dynamic range remain separate controls. No level boundaries or endpoints were changed.
'''
   if axis==3 and source.startswith('## 6.'):
    source='''## 6. Result and decision

The fixed depth0-to-depth4 contrast contains one assay from one protein. Its difference of 0.523308 remains descriptive; the corrected calculation reports no between-protein interval and no general directional claim. The lowest-depth group has six terminal positions in that protein, and the curve is not strictly monotonic.

The separate coarse-occupancy comparison is a different property. Its larger assay count does not provide replication of the effective-depth endpoint.
'''
   if source!=old:c['source']=source.splitlines(True);changes.append(dict(axis=axis,cell=i,kind='scientific_method_and_scope_prose'))
 p.write_text(json.dumps(book,indent=1,ensure_ascii=False)+'\n')
(HERE/'changed-cells.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Updated scientific helper, decision and scope in primary axes 3–7; saved outputs await actual execution.')
