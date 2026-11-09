# Notebook cell2
from pathlib import Path
import sys, json
root=next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'recovered_pipeline.py').is_file())
sys.path.insert(0,str(root))
import pandas as pd
from IPython.display import display, Markdown
from state_inputs import ensure_inputs
print(ensure_inputs())
import recovered_pipeline as rp
import notebook_support as ns

# Notebook cell4
initial,base=rp.modules()
import inspect
for f in [initial.get_hf_file_manifest,initial.load_target_results,initial.load_tahoe_metadata]:
    display(Markdown('```python\n'+inspect.getsource(f)+'\n```'))

# Notebook cell6
verification={}
for stage in rp.DEPENDENCIES:
    verification[stage]=rp.run_stage(stage, force=False)
    print(stage, 'completed')
display(verification)

# Notebook cell8
downloads=pd.read_json(rp.COMPUTED/'initial/artifacts/download_revisions.json')
with pd.option_context('display.max_rows',100,'display.max_colwidth',120):
    display(downloads[['repo','path','revision']])

# Notebook cell10
ns.display_json(rp.INITIAL/'artifacts/hypothesis_ledger.json')
ns.display_json(rp.INITIAL/'axis_ledger.json')
ns.display_json(rp.CONTINUED/'spectra_loop_state.json')

# Notebook cell12
ns.display_json(rp.COMPUTED/'initial/artifacts/all_scored_axis_discovery.json')
with pd.option_context('display.max_rows',200):
    display(pd.read_csv(rp.COMPUTED/'continued/artifacts/all_scored_axis_discovery_continued.csv'))

# Notebook cell14
display(pd.read_csv(rp.COMPUTED/'continued/artifacts/replogle_refined_axis_screen.csv'))
display(pd.read_csv(rp.COMPUTED/'continued/artifacts/multi_pathway_support_screen.csv'))
display(pd.DataFrame(json.loads((root/'axis_catalog.json').read_text())))

# Notebook cell16
display(Markdown((rp.CONTINUED/'state_spectra_report.md').read_text()))

