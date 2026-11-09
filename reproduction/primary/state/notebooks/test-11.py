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
verification=rp.run_stage('zeroshot')
ns.show_acquisition('zeroshot')

# Notebook cell6
ns.show_code('zeroshot',11)

# Notebook cell8
display(verification)

# Notebook cell9
curve=ns.compare_curve('spc_replogle_zeroshot_reactome_support_confirmation.csv', initial=False)
ns.show_curve(curve)

# Notebook cell11
ns.display_json(rp.CONTINUED/'artifacts/replogle_zeroshot_reactome_support_confirmation_decision.json')

