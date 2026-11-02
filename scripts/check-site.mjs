import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const read = (path) => readFile(new URL(path, root), "utf8");
for (const name of ["protocol.md", "finish.md", "agents.md"]) {
  const source = await read(`protocol/${name}`);
  const built = await read(`dist/${name}`);
  assert.equal(built, source, `${name} must publish the canonical source exactly`);
  assert.ok(source.startsWith("# "), `${name} needs a document title`);
  if (name !== "agents.md") {
    assert.match(source, /^Version: \d{4}-\d{2}-\d{2}\.\d+$/m, `${name} needs a protocol version`);
  }
}
const html = await read("dist/index.html");
for (const path of ["/protocol.md", "/finish.md", "/agents.md"]) {
  assert.ok(html.includes(path), `Homepage must link to ${path}`);
}
assert.ok(html.includes("https://spectra.yashaektefaie.com/data/findings.json"), "Registry must use the separately hosted index");
assert.ok(!html.includes("localhost"), "Production page must not link to localhost");
for (const id of ["run", "find", "submit"]) {
  assert.ok(html.includes(`id="tab-${id}"`), `Missing ${id} tab`);
  assert.ok(html.includes(`id="panel-${id}"`), `Missing ${id} panel`);
}
const guide = await read("dist/agents.md");
assert.ok(guide.includes("https://spectra.yashaektefaie.com/data/findings.json"), "Agent guide must use the separately hosted registry");
assert.ok(!guide.includes("(./data/findings.json)"), "Agent guide must not point to an absent local registry");
console.log("Built site checks passed: exact protocol copies, version fields, navigation, prompts, and registry links.");
