import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const dist = fileURLToPath(new URL("../.registry-build/", import.meta.url));
const pathFor = (url) => {
  assert.ok(url.startsWith("/") && !url.startsWith("//"));
  const p = resolve(dist, "." + url);
  assert.ok(p.startsWith(resolve(dist) + sep));
  return p;
};
const read = (url) => readFile(pathFor(url), "utf8");
const index = JSON.parse(await read("/registry/audits.json"));
const figureSources = JSON.parse(await read("/registry/figures/sources.json"));
const expected = ["ESMFold2", "STATE", "CONCH", "AlphaMissense"];
const decisions = new Set([
  "accepted",
  "rejected",
  "unresolved",
  "control",
  "exploratory",
  "off-target",
]);
assert.deepEqual(
  index.models.map((m) => m.name),
  expected,
);
assert.equal(figureSources.length, 8);
for (const f of figureSources) {
  const file = await readFile(pathFor("/registry/figures/" + f.file));
  assert.ok(file.subarray(0, 5).equals(Buffer.from("%PDF-")));
  assert.equal(
    createHash("sha256").update(file).digest("hex"),
    f.sha256,
    `Figure changed: ${f.file}`,
  );
}
// A shared header must actually render on every route, including the optional build.
const homepage = await readFile(fileURLToPath(new URL("../dist/index.html", import.meta.url)), "utf8");
const header = (page) => page.match(/<header class="site-header">[\s\S]*?<\/header>/)?.[0].replace(/ aria-current="page"/g, "");
assert.ok(header(homepage), "Homepage header is missing");
for (const route of ["/registry/", ...expected.map((name) => `/registry/${name.toLowerCase()}/`), ...index.investigations.map((a) => a.url)]) {
  const page = await read(route + "index.html");
  assert.equal(header(page), header(homepage), route + " has a different header");
  assert.ok(!page.includes("<img") && !page.includes("/registry/figures/"), route + " still displays a figure");
}
const files = new Set();
const notebookKinds = new Map();
for (const model of expected) {
  const entries = index.investigations.filter((a) => a.model === model);
  assert.equal(entries.length, 7);
  assert.equal(entries.filter((a) => a.scope === "primary").length, 1);
  assert.deepEqual(
    entries.filter((a) => a.scope === "additional").map((a) => a.figureRow),
    [1, 2, 3, 4, 5, 6],
  );
}
assert.equal(index.investigations.length, 28);
assert.equal(new Set(index.investigations.map((a) => a.id)).size, 28);
for (const record of index.investigations) {
  const page = await read(record.url + "index.html");
  assert.ok(!page.includes("How the code was recovered") && !page.includes("Source files and references"));
  const url = record.url.replace(/\/$/, "");
  const markdown = await read(url + ".md");
  const discrete = JSON.parse(await read(url + ".json"));
  assert.equal(record.id, discrete.id);
  assert.equal(record.axes.length, discrete.axes.length);
  assert.ok(record.axes.length > 0 && record.date && record.agent);
  assert.ok(record.summary?.trim() && page.includes(record.summary));
  assert.ok(!page.includes("<img") && !page.includes("/registry/figures/"));
  for (const [i, axis] of record.axes.entries()) {
    assert.ok(decisions.has(axis.status));
    for (const k of ["name", "explanation", "definition", "data", "code", "result"])
      assert.ok(
        typeof axis[k] === "string" && axis[k].trim(),
        record.id + "/" + k,
      );
    const notebookURL = record.url + "notebook-" + (i + 1) + "/";
    const notebookFile = `/registry/notebooks/${record.id}/test-${String(i + 1).padStart(2, "0")}.ipynb`;
    assert.ok(page.includes('href="' + notebookURL + '"') && markdown.includes(notebookURL));
    const viewer = await read(notebookURL + "index.html");
    const notebook = JSON.parse(await read(notebookFile));
    const meta = notebook.metadata.spectra;
    notebookKinds.set(meta.kind, (notebookKinds.get(meta.kind) || 0) + 1);
    assert.equal(notebook.nbformat, 4);
    assert.equal(meta.name, axis.name);
    assert.equal(meta.axis, i + 1);
    assert.equal(meta.auditId, record.id);
    assert.equal(header(viewer), header(homepage));
    assert.ok(viewer.includes('href="' + notebookFile + '"'));
    const outputs = notebook.cells.flatMap(c => c.outputs || []);
    assert.ok(outputs.every(out => out.output_type !== "error"));
    assert.ok(notebook.cells.every(c => c.cell_type !== "code" || c.execution_count > 0));
    if (meta.kind === "curve" || meta.kind === "comparison") {
      const plot = outputs.find(out => out.data?.["image/png"]);
      assert.ok(plot && viewer.includes(plot.data["image/png"]), notebookFile + " missing chart");
    } else if (meta.kind === "table") {
      assert.ok(outputs.length && !viewer.includes('class="notebook-chart"'));
    } else {
      assert.equal(meta.kind, "none");
      assert.ok(meta.note && !viewer.includes('class="notebook-chart"'));
    }
    assert.ok(page.includes(`id="axis-${i + 1}"`));
    assert.ok(markdown.includes(axis.name));
    const visible = page.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#(?:39|x27);/g, "'").replace(/&quot;/g, '"');
    assert.ok(visible.includes("<h2>" + axis.name + "</h2>"), record.id + " missing axis heading");
    assert.ok(visible.includes(axis.explanation), record.id + " missing explanation");
    assert.ok(visible.includes(axis.result), record.id + " missing result");
    assert.ok(page.includes(`class="decision ${axis.status}"`), record.id + " missing decision");
  }
  for (const r of [
    ...record.links,
    ...record.axes.flatMap((a) => a.links || []),
  ]) {
    assert.ok(r.label && r.href);
    if (r.href.startsWith("/")) files.add(r.href);
    else assert.equal(new URL(r.href).protocol, "https:");
  }
}
const manifest = JSON.parse(await read("/registry/evidence-manifest.json"));
const evidence = new Set([...files].filter(url => url.startsWith("/registry/evidence/")));
assert.equal(manifest.length, evidence.size, "Evidence inventory does not match the public links");
for (const item of manifest) {
  const url = "/registry/evidence/" + item.path;
  assert.ok(evidence.delete(url), url);
  const contents = await readFile(pathFor(url));
  assert.equal(contents.byteLength, item.bytes);
  assert.equal(createHash("sha256").update(contents).digest("hex"), item.sha256, url);
}
for (const url of files)
  assert.ok((await stat(pathFor(url))).size > 0, `Empty evidence file: ${url}`);
console.log(
  `Registry checks passed for 28 investigations, eight source PDFs and ${files.size} linked evidence files.`,
);

console.log("Executed notebooks by output:", Object.fromEntries(notebookKinds));
