"""Figures derived exclusively from newly computed result tables."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def run(root,stage='all'):
    root=Path(root);out=root/'computed/figures';out.mkdir(exist_ok=True,parents=True)
    names=['A8','A10'] if stage=='dose' else ['A9'] if stage=='secondary' else ['A8','A9','A10'] if stage=='all' else []
    for name in names:
        if not (root/f'computed/tahoe/{name}_curve.csv').exists():continue
        d=pd.read_csv(root/f'computed/tahoe/{name}_curve.csv');fig,ax=plt.subplots(figsize=(6,4));ax.errorbar(d.level,d['mean'],yerr=[d['mean']-d.ci_low,d.ci_high-d['mean']],marker='o',capsize=4)
        ax.set(xlabel='Mitochondrial burden quintile' if name=='A9' else 'Administered dose (µM)',ylabel='Signed-LFC Spearman',title=f'{name}: reconstructed original investigation')
        if name!='A9':ax.set_xticks([1,2,3],['5','0.5','0.05'])
        fig.tight_layout();fig.savefig(out/f'{name}_curve.png',dpi=150);plt.close(fig)
    if stage in ['all','distance'] and (root/'computed/replogle/distance_curve.csv').exists():
        d=pd.read_csv(root/'computed/replogle/distance_curve.csv');fig,ax=plt.subplots(figsize=(7,4))
        for metric,g in d.groupby('metric'):ax.errorbar(g.level,g['mean'],yerr=[g['mean']-g.ci_low,g.ci_high-g['mean']],marker='o',capsize=3,label=metric)
        axis=pd.read_csv(root/'computed/replogle/axis.csv').sort_values('level');ax.set_xticks(axis.level,axis.context);ax.set(xlabel='Increasing prospective distance',ylabel='Signed-LFC Spearman',title='Distance: original negative result');ax.legend();fig.tight_layout();fig.savefig(out/'distance_curve.png',dpi=150);plt.close(fig)
    if stage in ['all','magnitude'] and (root/'computed/replogle/magnitude_curve.csv').exists():
        d=pd.read_csv(root/'computed/replogle/magnitude_curve.csv');fig,ax=plt.subplots(figsize=(6,4));ax.errorbar(d.level,d['mean'],yerr=[d['mean']-d.ci_low,d.ci_high-d['mean']],marker='o',capsize=4);ax.set(xlabel='Expected magnitude: strongest → weakest',ylabel='Signed-LFC Spearman',title='Magnitude discovery; disjoint confirmation ineligible');fig.tight_layout();fig.savefig(out/'magnitude_curve.png',dpi=150);plt.close(fig)
