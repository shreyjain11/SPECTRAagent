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
SPECTRA_DATA = prepare_notebook('am-kimi-r1/test-06')
SPECTRA_HASHES = input_hashes(SPECTRA_DATA)

# Notebook cell 1
from pathlib import Path
import hashlib, json
ROOT=Path.cwd()
manifest=json.loads((ROOT/'INPUT_MANIFEST.json').read_text())
for item in manifest:
    path=ROOT/item['path']
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == SPECTRA_HASHES[str(path.relative_to(SPECTRA_DATA))]['sha256'], item['path']
print(f'{len(manifest)} retained evidence files verified.')
print('No individual measurements have been synthesized and no summary values are treated as raw data.')
