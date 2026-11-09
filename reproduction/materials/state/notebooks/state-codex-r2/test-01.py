# Notebook cell 0
from pathlib import Path
import sys
_search = [Path.cwd(), *Path.cwd().parents]
if '__file__' in globals():
    _script_directory = Path(__file__).resolve().parent
    _search = [_script_directory, *_script_directory.parents, *_search]
if globals().get('_registry') is not None:
    _search.append(Path(_registry))
_registry = next((q for p in _search for q in (p, p / 'reproduction')
                  if (q / 'prepare_inputs.py').is_file() and (q / 'data.json').is_file()), None)
assert _registry is not None, 'Open this notebook in the public SPECTRAagent checkout.'
sys.path.insert(0, str(_registry))
from prepare_inputs import prepare_notebook, input_hashes
SPECTRA_DATA = prepare_notebook('state-codex-r2/test-01')
SPECTRA_HASHES = input_hashes(SPECTRA_DATA)

# Notebook cell 1
from pathlib import Path
import sys,json,hashlib,io,os,tempfile,shutil,runpy,contextlib
import numpy as np,pandas as pd
from scipy.stats import spearmanr
from IPython.display import display,Image
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
root=next((p for p in [Path.cwd(),*Path.cwd().parents] if (p/'STATE_INPUTS.json').is_file()),None)
assert root is not None,'Extract the complete STATE bundle first.'
manifest={key.removeprefix('assets/'): value for key, value in SPECTRA_HASHES.items() if key.startswith('assets/')}
P=root/'assets'/'state-codex-r2'
for relative,meta in manifest.items():
    if relative.startswith('state-codex-r2'+'/'):
        assert hashlib.sha256((root/'assets'/relative).read_bytes()).hexdigest()==meta['sha256'],relative
print('Verified all run input and code hashes.')

# Notebook cell 2
def draw(data,x,y,group):
    rng=np.random.default_rng(7);rows=[]
    for keys,g in data.groupby([group,x],observed=True):
        v=pd.to_numeric(g[y],errors='coerce').dropna().values
        if not len(v):continue
        bs=np.array([rng.choice(v,len(v),True).mean() for _ in range(1000)])
        rows.append({group:keys[0],x:keys[1],'n':len(v),'mean':v.mean(),'lo':np.quantile(bs,.025),'hi':np.quantile(bs,.975)})
    t=pd.DataFrame(rows);display(t)
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained');levels=sorted(t[x].unique(),key=str)
    for name,g in t.groupby(group,observed=True):
        g=g.assign(xpos=g[x].map({v:i for i,v in enumerate(levels)})).sort_values('xpos')
        ax.errorbar(g.xpos,g['mean'],yerr=np.stack([g['mean']-g.lo,g.hi-g['mean']]),marker='o',capsize=2,label=str(name))
    ax.set_xticks(range(len(levels)),levels,rotation=25);ax.set(xlabel=x,ylabel=y);ax.legend(fontsize=7);ax.spines[['top','right']].set_visible(False)
    buf=io.BytesIO();fig.savefig(buf,format='png',dpi=120);plt.close(fig);display(Image(data=buf.getvalue()))

# Notebook cell 3
files=sorted(str(p.relative_to(P)) for p in P.rglob('*') if p.is_file() and '__pycache__' not in str(p))
print('Retained evidence:');print('\n'.join(files))
print('No curve or model result is recomputed. Summary numbers are not used as synthetic observations.')
