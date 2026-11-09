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
verification=rp.run_stage('controls')
ns.show_acquisition('controls')

# Notebook cell6
ns.show_code('controls',10)

# Notebook cell8
display(verification)

# Notebook cell9
ns.display_json(rp.COMPUTED/'continued/artifacts/controls_replogle_best_axis_regression.json')

# Notebook cell11
ns.display_json(rp.CONTINUED/'artifacts/controls_replogle_best_axis_regression.json')
ns.display_json(rp.CONTINUED/'artifacts/controls_replogle_best_axis_summary.json')

