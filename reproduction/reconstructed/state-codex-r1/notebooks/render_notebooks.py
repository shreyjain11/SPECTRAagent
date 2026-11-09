"""Export only fully executed source-to-decision notebooks and record validation."""
from pathlib import Path
import ast
import hashlib
import json
import nbformat
from nbconvert import HTMLExporter

ROOT=Path(__file__).resolve().parent
records=[]
for path in sorted(ROOT.glob('[0-9][0-9]-state-codex-r1-*.ipynb')):
    nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    for cell in code: ast.parse(cell.source)
    errors=[o for c in code for o in c.get('outputs',[]) if o.output_type=='error']
    if errors or any(c.execution_count is None for c in code):
        raise RuntimeError(f'{path.name}: every code cell must execute successfully before export')
    execution=nb.metadata.get('recovery_execution',{})
    if not execution.get('completed'):
        raise RuntimeError(f'{path.name}: missing successful execution receipt')
    if not any('wf.run_pipeline(ROOT)' in c.source for c in code):
        raise RuntimeError(f'{path.name}: real pipeline invocation missing')
    exporter=HTMLExporter(template_name='lab')
    body,_=exporter.from_notebook_node(nb)
    html=path.with_suffix('.html');html.write_text(body)
    images=sum('image/png' in o.get('data',{}) for c in code for o in c.get('outputs',[]))
    minimum_images=3 if path.name.startswith('04-') else 1
    if images<minimum_images:
        raise RuntimeError(f'{path.name}: expected at least{minimum_images} embedded calculated figures, got{images}')
    records.append({'notebook':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'html':html.name,'html_sha256':hashlib.sha256(html.read_bytes()).hexdigest(),
                    'code_cells':len(code),'code_cells_executed':len(code),'error_outputs':len(errors),
                    'embedded_pngs':images,'execution':execution,
                    'calculation_inputs':'verified public source bytes; derived stages recalculated by default',
                    'historical_aggregates':'comparison targets only'})
report={'status':'all_notebooks_executed_and_exported','notebooks':records,
        'scientific_execution_host':'exxact05','new_neural_inference':False,
        'note':'Default notebook execution requests fresh derived-stage calculations from verified original public source bytes. Pipeline receipts record the actual mode.'}
(ROOT/'NOTEBOOK_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
