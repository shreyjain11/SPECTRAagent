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
verification=rp.run_stage('parse')
ns.show_acquisition('parse')

# Notebook cell6
ns.show_code('parse',12)

# Notebook cell8
display(verification)

# Notebook cell9
curve=ns.compare_curve('spc_parse_fewshot_ligand_family_support.csv', initial=False)
ns.show_curve(curve)

# Notebook cell11
ns.display_json(rp.CONTINUED/'artifacts/parse_ligand_family_axis_freeze.json')
display(pd.read_csv(rp.COMPUTED/'continued/artifacts/spc_parse_fewshot_ligand_family_support_trends.csv'))
ledger=json.loads((rp.CONTINUED/'spectra_loop_state.json').read_text())
display([x for x in ledger['axes'] if 'PARSE' in x.get('axis_id','')])

