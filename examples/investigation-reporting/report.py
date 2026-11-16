#!/usr/bin/env python3
"""Validate and render an ordered investigation from executed notebooks.

This module renders saved artifacts. It never executes notebook analysis code.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import html
import json
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

SECTION = re.compile(r"^##\s+([1-6])(?:[.)])?\s+\S", re.MULTILINE)
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


class ReportError(ValueError):
    """The declared investigation does not match its saved evidence."""


def require(condition, message):
    if not condition:
        raise ReportError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def source_text(value):
    require(isinstance(value, str) or (isinstance(value, list) and all(isinstance(x, str) for x in value)),
            "Notebook text must be a string or list of strings")
    return value if isinstance(value, str) else "".join(value)


def contained(root, value, label):
    require(isinstance(value, str) and value.strip(), f"{label}: provide a relative file path")
    raw = Path(value)
    require(not raw.is_absolute(), f"{label}: absolute paths are not allowed")
    path = (root / raw).resolve()
    require(path.is_relative_to(root), f"{label}: path leaves the investigation directory")
    require(path.is_file(), f"{label}: file does not exist: {value}")
    return path


def timestamp(value, label):
    require(isinstance(value, str), f"{label}: provide an ISO timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ReportError(f"{label}: invalid timestamp") from error
    require(parsed.tzinfo is not None, f"{label}: timezone is required")
    return parsed


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportError(f"Cannot read JSON: {path.name}: {error}") from error


def validate_notebook(path, receipt, start, finish, label):
    raw = path.read_bytes()
    require(isinstance(receipt, dict), f"{label}: execution receipt must be an object")
    require(receipt.get("notebook_sha256") == digest(raw), f"{label}: execution receipt notebook hash differs")
    require(receipt.get("completed") is True and receipt.get("errors") == 0,
            f"{label}: execution receipt is not a completed error-free execution")
    require(timestamp(receipt.get("started_at"), label + " receipt start") == start and
            timestamp(receipt.get("finished_at"), label + " receipt finish") == finish,
            f"{label}: sequence times differ from execution receipt")
    require(isinstance(receipt.get("engine"), str) and receipt["engine"].strip(),
            f"{label}: execution engine is required")
    book = read_json(path)
    require(isinstance(book, dict) and book.get("nbformat") == 4 and isinstance(book.get("cells"), list), f"{label}: expected notebook format 4")
    require(all(isinstance(cell, dict) for cell in book["cells"]), f"{label}: malformed notebook cell")
    sections, code_by_section, section = [], {}, None
    codes = []
    for index, cell in enumerate(book["cells"]):
        if cell.get("cell_type") == "markdown":
            headings = SECTION.findall(source_text(cell.get("source", [])))
            require(len(headings) <= 1, f"{label}: put each numbered section in its own Markdown cell")
            if headings:
                section = int(headings[0])
                sections.append(section)
                code_by_section.setdefault(section, 0)
        elif cell.get("cell_type") == "code":
            codes.append(index)
            if section is not None:
                code_by_section[section] += 1
            outputs = cell.get("outputs", [])
            require(isinstance(outputs, list) and all(isinstance(x, dict) for x in outputs), f"{label}: malformed cell outputs")
            require(not any(output.get("output_type") == "error" for output in outputs),
                    f"{label}: saved error output in cell {index}")
            count = cell.get("execution_count")
            counted = type(count) is int and count > 0
            direct = cell.get("metadata", {}).get("direct_execution", {})
            directly_executed = (
                receipt["engine"] == "python_exec" and direct.get("completed") is True
                and direct.get("source_sha256") == digest(source_text(cell.get("source", [])).encode())
                and direct.get("outputs_sha256") == digest(canonical(outputs))
            )
            require(counted or directly_executed, f"{label}: cell {index} has no matching execution evidence")
    require(sections == [1, 2, 3, 4, 5, 6], f"{label}: expected exactly six numbered sections in order")
    require(all(code_by_section.get(i, 0) > 0 for i in range(1, 7)),
            f"{label}: every numbered section needs executable code")
    require(type(receipt.get("executed_cells")) is int and receipt["executed_cells"] == len(codes),
            f"{label}: execution receipt does not cover every code cell")
    if "executed_cell_indices" in receipt:
        require(receipt["executed_cell_indices"] == codes, f"{label}: receipt cell indexes differ from notebook")
    return book


def extract_curve(book, curve, label):
    if curve is None:
        return None
    require(isinstance(curve, dict) and set(curve) == {"cell", "output"},
            f"{label}: curve must specify zero-based cell and output indexes")
    ci, oi = curve["cell"], curve["output"]
    require(type(ci) is int and type(oi) is int and ci >= 0 and oi >= 0, f"{label}: invalid curve indexes")
    try:
        cell = book["cells"][ci]
        require(cell.get("cell_type") == "code", f"{label}: curve does not refer to a code cell")
        encoded = cell["outputs"][oi]["data"]["image/png"]
        data = base64.b64decode(source_text(encoded), validate=True)
    except (IndexError, KeyError, TypeError, binascii.Error, ValueError) as error:
        raise ReportError(f"{label}: requested saved PNG output is missing or invalid") from error
    require(data.startswith(PNG_HEADER) and len(data) >= 24 and data[12:16] == b"IHDR",
            f"{label}: saved output is not a PNG")
    require(int.from_bytes(data[16:20], "big") > 0 and int.from_bytes(data[20:24], "big") > 0,
            f"{label}: PNG has invalid dimensions")
    return data


def validate(sequence_path):
    sequence_path = Path(sequence_path).resolve()
    root, document = sequence_path.parent, read_json(sequence_path)
    require(isinstance(document, dict), "Sequence must be a JSON object")
    require(isinstance(document.get("title"), str) and document["title"].strip(), "Investigation title is required")
    require(isinstance(document.get("scope"), str) and document["scope"].strip(), "State the investigation scope")
    axes, ledger = document.get("axes"), document.get("expected_axis_ids")
    require(isinstance(axes, list) and axes, "At least one declared axis is required")
    require(isinstance(ledger, list) and ledger and all(isinstance(x, str) and x for x in ledger),
            "expected_axis_ids must be the complete ordered axis ledger")
    ids = [axis.get("id") for axis in axes if isinstance(axis, dict)]
    require(len(ids) == len(axes) and all(isinstance(x, str) and x for x in ids), "Each axis needs an id")
    require(len(set(ids)) == len(ids) and len(set(ledger)) == len(ledger), "Duplicate axis ids are not allowed")
    require(ids == ledger, "Axes are omitted, added, or reordered relative to expected_axis_ids")
    plan_created = None
    if document.get("predefined_plan") is not None:
        plan = read_json(contained(root, document["predefined_plan"], "predefined plan"))
        require(plan.get("expected_axis_ids") == ledger, "Axis ledger differs from predefined plan")
        plan_created = timestamp(plan.get("created_at"), "predefined plan created_at")
    validated, previous_start, previous_finish, notebook_paths = [], None, None, set()
    overlaps = False
    for axis in axes:
        label = axis["id"]
        for field in ["title", "result"]:
            require(isinstance(axis.get(field), str) and axis[field].strip(), f"{label}: {field} is required")
        require(type(axis.get("performed")) is bool, f"{label}: performed must be true or false")
        sources = axis.get("sources")
        require(isinstance(sources, list), f"{label}: sources must be a list")
        for item in sources:
            require(isinstance(item, dict) and isinstance(item.get("role"), str) and item["role"].strip(),
                    f"{label}: each source needs a factual role")
            parsed = urlparse(item.get("url", ""))
            require(parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password,
                    f"{label}: source URLs must be HTTPS without embedded credentials")
        if "curve_caption" in axis:
            require(isinstance(axis["curve_caption"], str) and axis["curve_caption"].strip() and axis.get("curve") is not None and axis["performed"],
                    f"{label}: curve_caption needs a performed axis with a saved curve")
        tables = []
        require(isinstance(axis.get("tables", []), list), f"{label}: tables must be a list")
        for table in axis.get("tables", []):
            require(isinstance(table, dict) and isinstance(table.get("role"), str) and table["role"].strip(),
                    f"{label}: each table needs a factual role")
            path = contained(root, table.get("path"), label + " table")
            require(path.suffix.lower() in {".csv", ".tsv", ".json", ".parquet"}, f"{label}: unsupported measurement file type")
            if "sha256" in table:
                require(table["sha256"] == digest(path.read_bytes()), f"{label}: table hash differs")
            tables.append({"path": path, "role": table["role"]})
        item = {"axis": axis, "curve": None, "notebook": None, "book": None, "tables": tables}
        if not axis["performed"]:
            require(all(axis.get(k) is None for k in ["notebook", "execution", "started_at", "finished_at", "curve"]),
                    f"{label}: an unperformed axis cannot claim execution, a notebook, or a curve")
        else:
            require(sources, f"{label}: a performed axis needs public source links")
            require("curve" in axis, f"{label}: declare a saved curve or explicitly use null")
            notebook = contained(root, axis.get("notebook"), label + " notebook")
            require(notebook.suffix == ".ipynb", f"{label}: notebook must have .ipynb extension")
            require(notebook not in notebook_paths, "Each tested axis needs its own notebook")
            notebook_paths.add(notebook)
            receipt_path = contained(root, axis.get("execution"), label + " execution")
            start, finish = timestamp(axis.get("started_at"), label + " start"), timestamp(axis.get("finished_at"), label + " finish")
            require(finish >= start, f"{label}: execution ends before it starts")
            require(previous_start is None or start >= previous_start, f"{label}: axis order contradicts recorded start times")
            overlaps |= previous_finish is not None and start < previous_finish
            previous_start, previous_finish = start, max(finish, previous_finish) if previous_finish else finish
            require(plan_created is None or plan_created <= start, f"{label}: predefined plan was recorded after execution started")
            receipt = read_json(receipt_path)
            require(receipt.get("analysis_id", label) == label, f"{label}: receipt names another axis")
            book = validate_notebook(notebook, receipt, start, finish, label)
            item.update(notebook=notebook, book=book, curve=extract_curve(book, axis["curve"], label))
        validated.append(item)
    return document, validated, overlaps


def status(item):
    if not item["axis"]["performed"]:
        return "Not performed"
    return "Tested · saved curve" if item["curve"] is not None else "Tested · no curve produced"


def execution_label(axis):
    start = (timestamp(axis["started_at"], "start").astimezone(timezone.utc) + timedelta(microseconds=500000)).replace(microsecond=0)
    finish = (timestamp(axis["finished_at"], "finish").astimezone(timezone.utc) + timedelta(microseconds=500000)).replace(microsecond=0)
    end_format = "%H:%M:%S" if start.date() == finish.date() else "%d %b %Y, %H:%M:%S"
    return f"Executed {start:%d %b %Y, %H:%M:%S}–{finish.strftime(end_format)} UTC."


def md_text(text):
    return re.sub(r"([\\`*{}\[\]<>])", r"\\\1", " ".join(text.splitlines()))


STYLE = """
:root{font-family:system-ui,-apple-system,sans-serif;color:#202020;background:#fff;line-height:1.55}
body{margin:0 auto;max-width:62rem;padding:1.5rem}h1{font-size:1.65rem;line-height:1.2}h2{font-size:1.1rem}
p{max-width:78ch}a{color:#174f87}a:focus-visible,summary:focus-visible{outline:3px solid #1768ac;outline-offset:4px}
.sequence{list-style:none;padding:0}.sequence>li{margin:0 0 1rem}.sequence>li:not(:last-child)::after{content:'↓  Next listed test';display:block;margin:.65rem 0 .4rem 1rem;color:#555;font-size:.85rem}
details{border:1px solid #b8b8b8;border-radius:5px;background:#fff}details:not([open]){max-width:30rem}
summary{padding:.8rem 1rem;cursor:pointer;font-weight:600}.status{display:block;font-size:.8rem;font-weight:400;color:#555;margin-left:1.15rem}
.axis-content{padding:0 1rem 1rem}figure{margin:1rem 0}img{display:block;max-width:100%;height:auto}figcaption,.execution{font-size:.85rem;color:#555}
.sources{padding-left:1.25rem}.sources a{overflow-wrap:anywhere}.axis-id{font-size:.8rem;color:#555}.links{display:flex;gap:1rem;flex-wrap:wrap}
@media(max-width:600px){body{padding:1rem}h1{font-size:1.4rem}summary{padding:.75rem}.axis-content{padding:0 .75rem .75rem}}
"""


NOTEBOOK_STYLE = """
.investigation-back{padding:1rem;max-width:74rem;margin:auto;font-family:system-ui,sans-serif}
.investigation-back a{color:#174f87}.investigation-back a:focus-visible{outline:3px solid #1768ac;outline-offset:3px}
.jp-Notebook{max-width:74rem;margin:auto;box-sizing:border-box}
.jp-Cell,.jp-Cell-inputWrapper,.jp-Cell-outputWrapper,.jp-InputArea,.jp-InputArea-editor,.jp-OutputArea,.jp-OutputArea-child{min-width:0;max-width:100%;box-sizing:border-box}
.jp-InputArea-editor,.jp-OutputArea-output{max-width:100%;overflow-x:auto}
.jp-RenderedHTMLCommon p,.jp-RenderedMarkdown p,.jp-RenderedHTMLCommon li{white-space:normal;overflow-wrap:break-word}
.jp-RenderedHTMLCommon pre,.jp-RenderedText pre,.jp-InputArea pre{white-space:pre;overflow-x:auto;max-width:100%}
.jp-RenderedHTMLCommon table{display:block;max-width:100%;overflow-x:auto;white-space:nowrap}
.jp-OutputArea-output img{max-width:100%;height:auto}
@media(max-width:600px){.jp-Notebook{padding:.5rem}.jp-InputPrompt,.jp-OutputPrompt{min-width:2.5rem;font-size:.7rem}}
"""


def render(sequence_path, output_path):
    document, items, overlaps = validate(sequence_path)
    output = Path(output_path).resolve()
    source_root = Path(sequence_path).resolve().parent
    require(not source_root.is_relative_to(output), "Output cannot be the source directory or an ancestor of it")
    protected = [Path(sequence_path).resolve()]
    for item in items:
        if item["notebook"] is not None:
            protected.extend([item["notebook"], (source_root / item["axis"]["execution"]).resolve()])
        protected.extend(table["path"] for table in item["tables"])
    if document.get("predefined_plan"):
        protected.append((source_root / document["predefined_plan"]).resolve())
    require(not any(path.is_relative_to(output) for path in protected), "Output cannot contain a source artifact")
    output.mkdir(parents=True, exist_ok=True)
    # Imports are presentation dependencies, never notebook analysis imports.
    import nbformat
    from nbconvert import HTMLExporter

    exporter = HTMLExporter(template_name="lab")

    def destination(relative):
        path = (output / relative).resolve()
        require(path.is_relative_to(output), "Generated path leaves the report directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    markdown = ["# " + md_text(document["title"]), "", md_text(document["scope"]), ""]
    cards, manifest = [], []
    for number, item in enumerate(items, 1):
        axis = item["axis"]
        safe_id = re.sub(r"[^a-z0-9_-]+", "-", axis["id"].lower()).strip("-") or "axis"
        stem = f"{number:02d}-{safe_id}"
        badge = f'<span class="status">{status(item)}</span>' if not axis["performed"] or item["curve"] is None else ""
        card = [f'<li><details id="{stem}"><summary>{number}. {html.escape(axis["title"])}',
                f'{badge}</summary><div class="axis-content">',
                f'<p class="axis-id">{html.escape(axis["id"])}</p><p>{html.escape(axis["result"])}</p>']
        record = {"id": axis["id"], "performed": axis["performed"], "curve_sha256": None, "tables": []}
        notebook_links = ""
        if axis["performed"]:
            raw_name, page_name = f"notebooks/{stem}.ipynb", f"notebooks/{stem}.html"
            shutil.copyfile(item["notebook"], destination(raw_name))
            page, _ = exporter.from_notebook_node(nbformat.reads(json.dumps(item["book"]), as_version=4))
            page = re.sub(r"<title>.*?</title>", "<title>" + html.escape(axis["title"]) + "</title>", page, count=1, flags=re.S)
            page = page.replace("</head>", '<style>' + NOTEBOOK_STYLE + '</style></head>', 1)
            page = re.sub(r'(<body\b[^>]*>)', lambda match: match[1] + '<nav class="investigation-back"><a href="../INVESTIGATION.html">Back to investigation</a></nav>', page, count=1)
            destination(page_name).write_text(page, encoding="utf-8")
            notebook_links = f'<p class="links"><a href="{page_name}">Read notebook</a><a href="{raw_name}" download>Download .ipynb</a></p>'
            card.append(f'<p class="execution">{execution_label(axis)}</p>')
            markdown.append(f'{number}. [{md_text(axis["title"])}]({page_name}) · [.ipynb]({raw_name})')
            record["notebook_sha256"] = digest(destination(raw_name).read_bytes())
            if item["curve"] is not None:
                curve_name = f"curves/{stem}.png"
                destination(curve_name).write_bytes(item["curve"])
                index = axis["curve"]
                caption = html.escape(axis.get("curve_caption", "Generated by the notebook."))
                card.append(f'<figure><img src="{curve_name}" alt="Saved curve for {html.escape(axis["title"], quote=True)}" loading="lazy" decoding="async"><figcaption>{caption}</figcaption></figure>')
                record.update(curve=curve_name, curve_sha256=digest(item["curve"]), source_curve_output=index)
            else:
                card.append('<p>No curve was produced for this tested axis. The executed notebook records the calculations and result.</p>')
        else:
            markdown.append(f'{number}. {md_text(axis["title"])} — not performed')
        if axis["sources"] or item["tables"]:
            card.append('<h2>Data and provenance</h2><ul class="sources">')
            for source in axis["sources"]:
                card.append(f'<li><a href="{html.escape(source["url"], quote=True)}">{html.escape(source["role"])}</a></li>')
            for table_number, table in enumerate(item["tables"], 1):
                table_name = f'tables/{stem}-{table_number:02d}{table["path"].suffix.lower()}'
                shutil.copyfile(table["path"], destination(table_name))
                record["tables"].append({"path": table_name, "sha256": digest(table["path"].read_bytes()), "role": table["role"]})
                card.append(f'<li><a href="{table_name}" download>{html.escape(table["role"])}</a> ({table["path"].suffix[1:].upper()})</li>')
            card.append('</ul>')
        if notebook_links:
            card.append(notebook_links)
        card.append('</div></details></li>')
        cards.append("\n".join(card))
        manifest.append(record)
    note = "Arrows show this recorded test order."
    if any(not item["axis"]["performed"] for item in items):
        note += " Unperformed axes are marked."
    if overlaps:
        note += " Execution windows overlap; order follows recorded starts."
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(document["title"])}</title><style>{STYLE}</style></head><body><main>'
            f'<h1>{html.escape(document["title"])}</h1><p>{html.escape(document["scope"])}</p><p>{note}</p>'
            '<p><a href="INVESTIGATION.md">Investigation list</a></p><ol class="sequence">' + "\n".join(cards) + '</ol></main></body></html>')
    destination("INVESTIGATION.html").write_text(page, encoding="utf-8")
    destination("index.html").write_text(page, encoding="utf-8")
    destination("INVESTIGATION.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    destination("render-manifest.json").write_text(json.dumps({"source_sha256": digest(Path(sequence_path).read_bytes()), "expected_axis_ids": document["expected_axis_ids"], "axes": manifest}, indent=2) + "\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate_only:
            _, items, _ = validate(args.sequence)
            print(f"Validated {len(items)} declared axes.")
        else:
            require(args.output is not None, "Specify --output or --validate-only")
            print(render(args.sequence, args.output))
    except (ReportError, OSError) as error:
        parser.exit(1, f"Report error: {error}\n")


if __name__ == "__main__":
    main()
