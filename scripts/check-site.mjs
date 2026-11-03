import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { relative, resolve } from "node:path";

const root = new URL("../", import.meta.url);
const dist = fileURLToPath(new URL("dist/", root));
const origin = "https://spectra.yashaektefaie.com";
const documents = ["protocol.md", "finish.md", "agents.md", "prompt.md", "submit.md"];
const read = (path) => readFile(new URL(path, root), "utf8");
const exists = async (path) => stat(path).then(() => true, () => false);
const normalize = (text) => text.replace(/\s+/g, " ").trim();
const decode = (text) => text.replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi, (_, entity) => {
  if (entity.startsWith("#")) {
    return String.fromCodePoint(entity[1].toLowerCase() === "x" ? parseInt(entity.slice(2), 16) : parseInt(entity.slice(1), 10));
  }
  return { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " " }[entity.toLowerCase()];
});

function checkReleaseText(text, name) {
  assert.doesNotMatch(text, /https?:\/\/(?:mcp\.spectra\.yashaektefaie\.com\b|spectra\.yashaektefaie\.com\/mcp\b)|spectra:\/\//i,
    `${name} must not direct users to retired MCP endpoints or resources`);
  assert.doesNotMatch(text, /\b(?:get|list|search|validate|submit|publish|promote|audit|suggest)_spectra_[a-z0-9_]+\b/i,
    `${name} must use HTTPS instructions, not retired MCP tools`);
  assert.doesNotMatch(text, /\/api\/[^\s<>"'`)]*\b(?:publish|promote)(?:[/?#\s<>"'`)]|$)/i,
    `${name} must not call an automatic-publication route`);
  assert.doesNotMatch(text, /\blocalhost\b|\b127\.0\.0\.1\b|\b0\.0\.0\.0\b|file:\/\/|\/(?:Users|home|private|tmp|root)\/|[A-Za-z]:\\(?:Users|Windows)\\/i,
    `${name} must not expose local addresses or private filesystem paths`);
}

async function checkMarkdownLinks(text, name) {
  const targets = [
    ...Array.from(text.matchAll(/!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+["'][^\n]*["'])?\s*\)/g), (m) => m[1]),
    ...Array.from(text.matchAll(/^\s{0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)/gm), (m) => m[1]),
  ];
  for (let target of targets) {
    target = decode(target.replace(/^<|>$/g, ""));
    if (!target || target.startsWith("#")) continue;
    if (/^[a-z][a-z0-9+.-]*:/i.test(target) || target.startsWith("//")) {
      if (/^https?:/i.test(target) || target.startsWith("//")) {
        const url = new URL(target, origin);
        if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
          assert.equal(url.origin, origin, `${name}: API links must use the canonical HTTPS host`);
        }
      }
      continue;
    }
    const url = new URL(target, `https://static-preview.invalid/${name}`);
    assert.ok(url.pathname !== "/api" && !url.pathname.startsWith("/api/"),
      `${name}: API links must use the canonical HTTPS host, not a local relative URL`);
    const pathname = decodeURIComponent(url.pathname);
    const builtPath = resolve(dist, "." + pathname, pathname.endsWith("/") ? "index.html" : "");
    assert.ok(!relative(dist, builtPath).startsWith(".."), `${name}: link escapes the built site: ${target}`);
    assert.ok(await exists(builtPath), `${name}: relative link has no built target: ${target}`);
    assert.ok((await stat(builtPath)).isFile(), `${name}: relative link must resolve to a built file: ${target}`);
  }
}

const docs = {};
for (const name of documents) {
  const source = await read(`protocol/${name}`);
  docs[name] = await read(`dist/${name}`);
  assert.equal(docs[name], source, `${name} must publish its canonical source exactly`);
  if (name === "protocol.md" || name === "finish.md") {
    assert.match(source, /^Version: \d{4}-\d{2}-\d{2}\.\d+$/m, `${name} needs a protocol version`);
  }
  if (name === "prompt.md") {
    assert.doesNotMatch(source, /^\s*#{1,6}\s/m, "prompt.md must contain the raw starting prompt, without a heading");
  } else {
    assert.match(source, /^# /, `${name} needs a document title`);
  }
  checkReleaseText(source, name);
  await checkMarkdownLinks(source, name);
}

const html = await read("dist/index.html");
assert.ok(html.includes('href="/registry/"'), "Homepage must link to the hosted manuscript registry");
checkReleaseText(decode(html), "Homepage");
const attributes = (tag) => Object.fromEntries(Array.from(tag.matchAll(/([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g), (m) => [m[1], decode(m[2] ?? m[3])]));
const buttons = Array.from(html.matchAll(/<button\b[^>]*>/gi), (m) => attributes(m[0]));
for (const match of html.matchAll(/<a\b[^>]*>/gi)) {
  const href = attributes(match[0]).href;
  if (!href) continue;
  const url = new URL(href, "https://static-preview.invalid/");
  if (url.pathname === "/api" || url.pathname.startsWith("/api/")) {
    assert.equal(url.origin, origin, "Homepage API links must use the canonical HTTPS host");
  }
}
assert.equal(buttons.filter((button) => button.role === "tab").length, 3, "Homepage needs exactly three task tabs");
assert.equal(buttons.filter((button) => button["data-copy-target"]).length, 3, "Each task needs its own copy button");

function element(id) {
  const match = html.match(new RegExp(`<([a-z][\\w-]*)\\b[^>]*\\bid=["']${id}["'][^>]*>([\\s\\S]*?)<\\/\\1>`, "i"));
  assert.ok(match, `Missing homepage element: ${id}`);
  return { attributes: attributes(match[0].slice(0, match[0].indexOf(">") + 1)), text: decode(match[2].replace(/<[^>]*>/g, "")) };
}

const prompts = {};
for (const id of ["run", "find", "submit"]) {
  const tab = buttons.find((button) => button.id === `tab-${id}`);
  assert.ok(tab, `Missing ${id} tab`);
  assert.equal(tab["aria-controls"], `panel-${id}`, `${id} tab must select its panel`);
  const panel = element(`panel-${id}`).attributes;
  assert.equal(panel.role, "tabpanel", `${id} panel must be a tab panel`);
  assert.equal(panel["aria-labelledby"], `tab-${id}`, `${id} panel must identify its tab`);
  assert.ok(buttons.some((button) => button["data-copy-target"] === `prompt-${id}`), `Missing ${id} prompt copy target`);
  prompts[id] = element(`prompt-${id}`).text;
}
assert.equal(normalize(prompts.run), normalize(docs["prompt.md"]), "Run copy must match the paper's raw starting prompt");
for (const required of [`${origin}/protocol.md`, `${origin}/finish.md`, "Available compute and access:"]) {
  assert.ok(prompts.run.includes(required), `Run prompt is missing ${required}`);
}
assert.ok(prompts.find.includes(`${origin}/api/models`), "Find prompt must start from the hosted model index");
assert.ok(prompts.submit.includes(`${origin}/submit.md`), "Submit prompt must use the hosted submission guide");
assert.ok(buttons.some((button) => /Copy agent guide/i.test(button["aria-label"] ?? "")), "Homepage needs the agent-guide copy action");
assert.equal(element("agent-guide-link").attributes.href, `${origin}/agents.md`, "The handoff link must copy the canonical agent guide, including in local previews");

for (const endpoint of ["models", "submissions/schema", "submissions/validate", "submissions"]) {
  assert.ok(docs["agents.md"].includes(`${origin}/api/${endpoint}`), `Agent guide is missing the hosted ${endpoint} route`);
}
for (const path of ["api", "data/findings.json"]) {
  assert.ok(!(await exists(resolve(dist, path))), `The static release must not bundle or replace the hosted ${path}`);
}
console.log("Release checks passed: five exact documents, paper prompt, task navigation, HTTPS routes, and resolvable local links.");
