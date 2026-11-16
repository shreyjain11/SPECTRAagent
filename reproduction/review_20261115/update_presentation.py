"""Render reviewed Markdown without executing or changing scientific cells.

The previous execution receipts are retained. Every revised receipt separates
that execution from the later prose/layout correction.
"""
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from nbconvert.filters import markdown2html

ROOT = Path(__file__).resolve().parents[1]
BASE = 'dfe2a55acebe3ba00df217e1f18b8148de6ff78f'
CSS = '''
/* Notebook presentation: preserve the recorded code, tables and figures. */
body.jp-Notebook { margin: 0 auto; max-width: 1280px; padding: 24px 20px 48px; }
.jp-Cell { margin-bottom: 14px; }
.jp-RenderedMarkdown { line-height: 1.55; overflow-wrap: anywhere; }
.jp-RenderedMarkdown p { margin: 0 0 1em; }
.jp-RenderedMarkdown h2 { margin-top: 1.6em; margin-bottom: .7em; scroll-margin-top: 20px; }
.jp-InputArea-editor { min-width: 0; overflow-x: auto !important; }
.jp-InputArea-editor pre { white-space: pre; padding-bottom: 8px; }
.jp-OutputArea-output { min-width: 0; max-width: 100%; overflow-x: auto; }
.jp-RenderedHTMLCommon table { margin: .6em 0 1em; }
.jp-RenderedText pre { padding-bottom: 8px; white-space: pre-wrap; word-break: normal; overflow-wrap: normal; }
.jp-RenderedImage img { max-width: 100%; height: auto; }
.notebook-navigation { margin: 0 0 20px 78px; font: 14px system-ui, sans-serif; }
.notebook-navigation a { color: #155c9b; }
@media (max-width: 640px) {
  body.jp-Notebook { padding: 16px 10px 32px; }
  .jp-InputPrompt, .jp-OutputPrompt { min-width: 42px; flex-basis: 42px; font-size: 10px; }
  .notebook-navigation { margin-left: 42px; }
}
'''

def sha(data): return hashlib.sha256(data).hexdigest()
def canonical(obj): return sha(json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
def read(path): return json.loads((ROOT / path).read_text())
def write(path, obj):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
def original(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:reproduction/{path}'], cwd=ROOT.parent)
def digest(path): return sha((ROOT / path).read_bytes())

def cell_hashes(book):
    return [{'notebook_cell': i, 'execution_count': c['execution_count'],
             'source_sha256': sha(''.join(c['source']).encode()),
             'outputs_sha256': canonical(c['outputs']), 'cell_sha256': canonical(c)}
            for i, c in enumerate(book['cells']) if c['cell_type'] == 'code']

def replace_markdown(page, old, new):
    # Only replace the content of Markdown notebook cells. Scientific code,
    # captured outputs, figures, scripts and the original styles stay byte-exact.
    starts = list(re.finditer(r'<div class="jp-Cell jp-(?:Markdown|Code)Cell\b', page))
    blocks = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1].start() if pos + 1 < len(starts) else page.index('</main>', start.start())
        blocks.append((start.start(), end, page[start.start():end]))
    assert len(blocks) == len(old['cells']) == len(new['cells'])
    for i in reversed(range(len(blocks))):
        if old['cells'][i]['cell_type'] != 'markdown': continue
        source = ''.join(new['cells'][i]['source'])
        if source == ''.join(old['cells'][i]['source']): continue
        start, end, block = blocks[i]
        opening = re.search(r'<div class="jp-RenderedHTMLCommon jp-RenderedMarkdown jp-MarkdownOutput"[^>]*>', block)
        assert opening, i
        depth = 1
        closing = None
        for match in re.finditer(r'</?div\b[^>]*>', block[opening.end():]):
            depth += -1 if match.group(0).startswith('</') else 1
            if depth == 0:
                closing = opening.end() + match.start()
                break
        assert closing is not None, i
        block = block[:opening.end()] + '\n' + markdown2html(source) + '\n' + block[closing:]
        page = page[:start] + block + page[end:]
    return page

def output_typography(page):
    """Separate joined words/numbers only in rendered human-readable outputs.

    Notebook outputs stay exact. The HTML change cannot alter a non-space
    character, a number or a program/input cell.
    """
    def fix(match):
        old = match.group(0)
        new = re.sub(r'\b(the|The|and|section|complete|than|fixed)(?=\d)', r'\1 ', old)
        assert re.sub(r'\s', '', new) == re.sub(r'\s', '', old)
        return new
    return re.sub(r'<div[^>]*class="[^"]*(?:jp-RenderedText|jp-RenderedMarkdown jp-OutputArea-output)[^>]*>.*?</div>', fix, page, flags=re.S)

def main():
    index = read('inline/index.json')
    reviewed = []
    for item in index['analyses']:
        name, page_path, receipt_path = item['notebook'], item['html'], item['validation']
        old_nb = original(name)
        old = json.loads(old_nb)
        book = read(name)
        prior, current = cell_hashes(old), cell_hashes(book)
        assert prior == current, (item['id'], 'scientific cells changed')
        old_page = original(page_path)
        page = output_typography(replace_markdown(old_page.decode(), old, book))
        title = next(''.join(c['source']).splitlines()[0].removeprefix('# ') for c in book['cells'] if c['cell_type'] == 'markdown')
        page = re.sub(r'<title>.*?</title>', '<title>' + html.escape(title) + '</title>', page, count=1, flags=re.S)
        page = page.replace('</head>', '<style id="spectra-notebook-layout">' + CSS + '</style>\n</head>', 1)
        page = re.sub(r'(<body\b[^>]*>)', r'\1\n<nav class="notebook-navigation" aria-label="Notebook navigation"><a href="../../index.html">All notebooks</a></nav>', page, count=1)
        (ROOT / page_path).write_text(page)
        identifier = item['id']
        base = 'review_20261115/presentation/' + identifier.replace('/', '-')
        old_receipt_path = base + '.previous-execution.json'
        old_record_path = base + '.previous-inline-implementation.json'
        revision_path = base + '.revision.json'
        old_receipt = json.loads(original(receipt_path))
        write(old_receipt_path, old_receipt)
        old_record = json.loads(original('analyses/' + identifier + '.json'))
        write(old_record_path, old_record['inline_implementation'])
        changed = [i for i, (a, b) in enumerate(zip(old['cells'], book['cells'])) if a != b]
        revision = {'analysis_id': identifier, 'original_commit': BASE,
                    'kind': 'reviewed_markdown_and_layout', 'scientific_reexecution': False,
                    'original_artifacts': {'notebook': {'path': name, 'sha256': sha(old_nb)}, 'html': {'path': page_path, 'sha256': sha(old_page)}},
                    'published_artifacts': {'notebook': {'path': name, 'sha256': digest(name)}, 'html': {'path': page_path, 'sha256': digest(page_path)}},
                    'modified_markdown_cells': changed, 'original_code_cells': prior, 'published_code_cells': current,
                    'previous_inline_implementation': {'path': old_record_path, 'sha256': digest(old_record_path)},
                    'layout': 'Readable paragraph spacing; whitespace-only corrections to joined words/numbers in rendered outputs; scrollable code and wide outputs; responsive image width; descriptive page title and index link.'}
        write(revision_path, revision)
        receipt = dict(old_receipt)
        receipt.update(notebook_sha256=digest(name), html_sha256=digest(page_path))
        receipt['presentation_revision'] = {
            'scientific_reexecution': False,
            'original_execution_evidence': {'path': old_receipt_path, 'sha256': digest(old_receipt_path)},
            'correction_record': {'path': revision_path, 'sha256': digest(revision_path)}}
        receipt['presentation_note'] = 'The original execution is retained separately. This revision changes explanatory Markdown and HTML layout; scientific code, saved numbers and figures are unchanged.'
        write(receipt_path, receipt)
        record_path = 'analyses/' + identifier + '.json'
        record = read(record_path)
        impl = record['inline_implementation']
        impl.update(published_notebook_sha256=digest(name), published_html_sha256=digest(page_path))
        current_record = record['current_inline_analysis']
        current_record['notebook_sha256'] = digest(name)
        if 'evidence' in current_record:
            evidence = current_record['evidence']
            evidence['notebook_sha256'] = digest(name)
            evidence['execution_record_sha256'] = digest(receipt_path)
        current_record['interpretation_review'] = {
            'scope': 'Individual notebook prose, calculations and saved outputs reviewed; no fresh inference or complete scientific reexecution.',
            'notes': 'Read the reviewed Markdown beside the saved outputs; saved code-generated labels do not supersede the stated limitations.',
            'presentation_record': revision_path}
        write(record_path, record)
        reviewed.append({'id': identifier, 'modified_markdown_cells': changed, 'scientific_cells_unchanged': True, 'html': page_path, 'notebook': name})
    write('review_20261115/presentation-summary.json', {'base_commit': BASE, 'entries': reviewed, 'entries_rendered': len(reviewed), 'scientific_reexecution': False})
    print(f'Rendered {len(reviewed)} entries; scientific code, saved outputs and figures preserved.')

if __name__ == '__main__': main()
