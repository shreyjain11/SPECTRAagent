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
verification=rp.run_stage('ontology')
ns.show_acquisition('ontology')

# Notebook cell6
ns.show_code('ontology',15)

# Notebook cell8
display(verification)

# Notebook cell9
curve=ns.compare_curve('spc_multi_pathway_go_bp.csv', initial=False)
ns.show_curve(curve)

# Notebook cell11
screen=pd.read_csv(rp.CONTINUED/'artifacts/multi_pathway_support_screen.csv')
display(screen[screen.collection=='GO_BP'])
display(pd.read_csv(rp.COMPUTED/'continued/artifacts/spc_multi_pathway_go_bp_trends.csv'))

