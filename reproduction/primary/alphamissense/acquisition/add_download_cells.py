"""Add executable acquisition cells while retaining original analysis outputs."""
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT.parent
intro = '''## Download and prepare the public source data

The cells below are runnable **reconstructed download recipes**, not a claim to recover the original shell history. The prediction files are official released AlphaMissense scores; no new model inference is needed. Defaults verify the supplied inputs and leave the saved historical analysis intact.

Set `RUN_DOWNLOADS = True` to fetch this axis's public inputs, verify their versions/hashes, and prepare the exact files consumed by the later calculations. Downloads go to `DOWNLOAD_CACHE`; validated results are staged under `am-primary/inputs`. Existing inputs are retained only after equality checks. A changed public file causes a clear error rather than substitution. The source selection and every path bridge are implemented in [reproduce_downloads.py](../acquisition/reproduce_downloads.py), with pinned addresses in [download_sources.json](../acquisition/download_sources.json).

**Verified ClinVar snapshot:** [clinvar_20260606.vcf.gz](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/archive_2.0/2026/clinvar_20260606.vcf.gz), 196,569,024 bytes. Its full SHA256 matches the original `c5bb136e1ac476d390d8110905e8224126ce7d43d5eae0e0bfe689fbe96b8726`. This resolves the earlier unknown-date limitation. The clinical preparation invokes the original `build_benchmark.py` with only its data/output paths changed; it requires `bcftools` on PATH. For example, install it in your analysis environment with `conda install -c conda-forge -c bioconda bcftools` before enabling the clinical download cell.

For the DMS axes, the helper extracts the original 73 assay files from the versioned ProteinGym v1.3 archive and selects the original 64 accessions from the released prediction file, checking all selected input bytes/content. It preserves the recorded final assay selection; the earlier rejected preparation attempts remain shown below. Optional MSA downloads feed the original alignment functions directly through `--msa-dir`.

The current checks actually downloaded ClinVar (197 MB), the DMS archive (43 MB) and gnomAD (5 MB), and checked their full hashes and all 73 DMS members. The large AlphaMissense releases and MSA archive were checked by endpoint metadata here; their full download functions remain opt-in. [Official AlphaMissense source](https://github.com/google-deepmind/alphamissense) · [Official ProteinGym download instructions](https://github.com/OATML-Markslab/ProteinGym#resources).
'''

setup = '''from pathlib import Path
import os, sys, json
from IPython.display import display, Markdown
# Locate the bundle from the notebook folder, model folder, or recovery root.
search = [Path.cwd(), *Path.cwd().parents]
candidates = [q for p in search for q in [p, p/'alphamissense']]
AM_BUNDLE = next((q for q in candidates if (q/'acquisition/reproduce_downloads.py').is_file() and (q/'am-primary').is_dir()), None)
if AM_BUNDLE is None:
    raise RuntimeError('Open this notebook from its recovery bundle, or set AM_BUNDLE to the alphamissense folder.')
AM_BUNDLE = AM_BUNDLE.resolve()
os.chdir(AM_BUNDLE/'am-primary')
sys.path.insert(0, str(AM_BUNDLE/'acquisition'))
from reproduce_downloads import sources, check_packaged_inputs, prepare_axis, rebuild_uniref_search
print('Analysis folder:', Path.cwd())
print('Source preparation helper:', AM_BUNDLE/'acquisition/reproduce_downloads.py')
'''

def cells(axis):
    keys = ['clinvar', 'am_hg38', 'gnomad' if axis == 2 else 'uniref'] if axis < 3 else ['proteingym_dms', 'am_substitutions', 'proteingym_msa']
    describe = f'''for key in {keys!r}:
    spec = sources()[key]
    display(Markdown(f"**{{key}}** — {{spec['version']}}\\n\\n[Download address]({{spec['url']}})\\n\\nExpected bytes: `{{spec.get('bytes')}}`; SHA256: `{{spec.get('sha256') or 'selected-member validation; see manifest'}}`."))
display(check_packaged_inputs({axis}))
verified = json.loads((AM_BUNDLE/'acquisition/download_verification.json').read_text())
display([{{k:v for k,v in x.items() if k in ['key','bytes','sha256']}} for x in verified])
'''
    fetch = f'''RUN_DOWNLOADS = False
DOWNLOAD_FULL_MSAS = False  # Additional 1.5 GB download; required only for fresh alignment reconstruction.
DOWNLOAD_CACHE = AM_BUNDLE/'acquisition/downloads'  # May be changed to a scratch disk.
if RUN_DOWNLOADS:
    prepared = prepare_axis({axis}, cache=DOWNLOAD_CACHE, include_alignments=DOWNLOAD_FULL_MSAS)
    display({{k: ({{kk:vv for kk,vv in v.items() if kk != 'members'}} if isinstance(v,dict) else v) for k,v in prepared.items()}})
    print('Validated inputs are connected to the existing calculation cells below.')
else:
    print('Bulk downloads are disabled in this saved run; exact packaged inputs were checked above.')
'''
    extra = '''REBUILD_ALIGNMENTS = False  # Linux x86-64; runs the original 66-MSA feature computation.
if REBUILD_ALIGNMENTS:
    import subprocess
    msa_dir = AM_BUNDLE/'upstream_checks/downloaded_msa'
    if not msa_dir.is_dir():
        raise RuntimeError('First enable RUN_DOWNLOADS and DOWNLOAD_FULL_MSAS above.')
    subprocess.run([sys.executable, str(AM_BUNDLE/'upstream_checks/run_upstream.py'),
                    '--all', '--resume', '--msa-dir', str(msa_dir)], check=True)
    print('Fresh upstream outputs are in upstream_checks/rebuilt; the Linux reconstruction cells below consume them.')
else:
    print('Fresh alignment reconstruction is disabled here. The saved upstream section states its platform and recorded-array reuse explicitly.')
'''
    if axis == 1:
        extra = '''REBUILD_UNIREF_SEARCH = False  # Official archived release is 268 GB, plus database/search scratch space.
FRESH_UNIREF_HITS = None
if REBUILD_UNIREF_SEARCH:
    search_result = rebuild_uniref_search(cache=DOWNLOAD_CACHE)
    FRESH_UNIREF_HITS = Path(search_result['output'])
    display(search_result)
else:
    print('Using the supplied complete original UniRef50 search hits. The optional fresh-search function pins release2026_01 and validates output identity.')
'''
    if axis == 2:extra = "print('Clinical join and gnomAD preparation feed inputs/clinvar, used directly by the original score/bin/bootstrap code below.')"
    result = [nbformat.v4.new_markdown_cell(intro),nbformat.v4.new_code_cell(setup),
              nbformat.v4.new_code_cell(describe),nbformat.v4.new_code_cell(fetch),nbformat.v4.new_code_cell(extra)]
    for i,c in enumerate(result):c['id']=f'public-download-axis{axis}-{i}';c.metadata['acquisition_recipe']=True
    return result

for axis in range(1,8):
    path = BUNDLE/f'am-primary/axis-{axis}.ipynb'
    nb = nbformat.read(path,as_version=4)
    nb.cells = [c for c in nb.cells if not c.metadata.get('acquisition_recipe')]
    for c in nb.cells:
        if c.cell_type != 'markdown':continue
        if '**Unrecovered acquisition detail:**' in c.source:
            c.source = c.source.split('\n\n**Unrecovered acquisition detail:**')[0] + '\n\n**Acquisition update:** the exact June 6, 2026 ClinVar archive file was downloaded and its complete SHA256 matched the original source. The executable recipe above uses that dated URL and the original join program.'
        if '**Acquisition record:**' in c.source:
            c.source = c.source.split('\n\n**Acquisition record:**')[0] + '\n\n**Acquisition update:** the executable recipe above downloads ProteinGym v1.3 and verifies every selected assay member against the original input. These reconstructed commands are sufficient to retrieve the identified data; the earlier shell probes are preserved as history.'
    nb.cells[1:1] = cells(axis)
    if axis == 1:
        for c in nb.cells:
            if c.cell_type == 'code' and 'with __import__("gzip").open(f"{WORK}/msa_hits.m8.gz", "rt") as fh:' in c.source:
                c.source = c.source.replace('with __import__("gzip").open(f"{WORK}/msa_hits.m8.gz", "rt") as fh:',
                    'with (open(FRESH_UNIREF_HITS, "rt") if globals().get("FRESH_UNIREF_HITS") else __import__("gzip").open(f"{WORK}/msa_hits.m8.gz", "rt")) as fh:')
    nbformat.write(nb,path)
print('Added executable acquisition recipes to seven primary notebooks.')
