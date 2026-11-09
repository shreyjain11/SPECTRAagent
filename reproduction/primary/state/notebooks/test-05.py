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
verification=rp.run_stage('replogle')
ns.show_acquisition('replogle')

# Notebook cell6
ns.show_code('replogle',5)

# Notebook cell8
display(verification)

# Notebook cell9
curve=ns.compare_curve('spc_state_replogle_reactome_pathway_log_train_support_v2.csv', initial=False)
ns.show_curve(curve)

# Notebook cell11
screen=pd.read_csv(rp.CONTINUED/'artifacts/replogle_refined_axis_screen.csv')
display(screen[screen.feature=='reactome_pathway_train_support_log_mean'])
ns.display_json(rp.CONTINUED/'artifacts/replogle_refined_axis_screen.json')

