"""Export the five genuinely executed notebooks, retaining actual figures/code."""
from pathlib import Path
import ast,hashlib,json
import nbformat
from nbconvert import HTMLExporter
ROOT=Path(__file__).resolve().parent
records=[]
for path in sorted(ROOT.glob('[0-9][0-9]-state-codex-r2-*.ipynb')):
    nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
    cells=[c for c in nb.cells if c.cell_type=='code']
    for cell in cells:ast.parse(cell.source)
    errors=[o for c in cells for o in c.get('outputs',[]) if o.output_type=='error']
    execution=nb.metadata.get('recovery_execution',{})
    if errors or any(c.execution_count is None for c in cells) or not execution.get('completed'):
        raise RuntimeError(f'{path.name}: successful execution of every code cell required')
    images=sum('image/png' in o.get('data',{}) for c in cells for o in c.get('outputs',[]))
    minimum={1:2,2:1,3:1,4:1,5:0}[int(path.name[:2])]
    if images<minimum:raise RuntimeError(f'{path.name}: expected{minimum} calculated figures; got{images}')
    html=path.with_suffix('.html');body,_=HTMLExporter(template_name='lab').from_notebook_node(nb);html.write_text(body)
    records.append({'notebook':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'html':html.name,'html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),'code_cells':len(cells),'code_cells_executed':len(cells),'error_outputs':len(errors),'embedded_pngs':images,'execution':execution,'stage':nb.metadata['state_reconstruction']['stage'],'historical_outcomes':'comparison targets and original stopping decisions only'})
if len(records)!=5:raise RuntimeError('Expected exactlyfive notebooks')
report={'status':'all_notebooks_executed_and_exported','scientific_execution_host':'exxact05','notebooks':records,'default_policy':'force_source_calculation','unscored_original_candidates':'actual input/eligibility/design diagnostics; no invented outcome curves'}
(ROOT/'NOTEBOOK_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
