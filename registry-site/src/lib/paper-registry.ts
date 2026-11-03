import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const bundle = process.env.SPECTRA_REGISTRY_BUNDLE;
if (!bundle) throw new Error("Set SPECTRA_REGISTRY_BUNDLE to the extracted manuscript collection.");
const readJSON = (file: string) => JSON.parse(readFileSync(resolve(bundle,file),"utf8"));
const audits = readJSON("investigations.json");
const figures: { model:string; version:string; file:string }[] = readJSON("public/registry/figures/sources.json");

export type EvidenceLink = { label: string; href: string };
export type Axis = {
  name: string;
  status: string;
  definition: string;
  data: string;
  code: string;
  result: string;
  links?: EvidenceLink[];
};
export type Investigation = {
  id: string;
  model: string;
  title: string;
  source: string;
  date_note?: string;
  code_provenance?: string;
  eligibility?: string;
  date: string;
  agent: string;
  scope: "primary" | "additional";
  figureRow?: number;
  axes: Axis[];
  links: EvidenceLink[];
};
export const investigations: Investigation[] = audits as Investigation[];
export const models = [
  {
    slug: "esmfold2",
    name: "ESMFold2",
    figure: 2,
    field: "Protein structure",
    task: "Protein structure prediction from amino-acid sequence.",
  },
  {
    slug: "state",
    name: "STATE",
    figure: 3,
    field: "Perturbation biology",
    task: "Gene-expression response to genetic or chemical perturbations.",
  },
  {
    slug: "conch",
    name: "CONCH",
    figure: 4,
    field: "Computational pathology",
    task: "Zero-shot classification of colorectal tissue images.",
  },
  {
    slug: "alphamissense",
    name: "AlphaMissense",
    figure: 5,
    field: "Variant effects",
    task: "Missense variant pathogenicity and functional effects.",
  },
];
export const statusNames: Record<string, string> = {
  accepted: "Accepted",
  rejected: "Rejected",
  unresolved: "Unresolved",
  control: "Control",
  exploratory: "Exploratory",
  "off-target": "Off-target",
};
export function modelAudits(name: string) {
  return investigations.filter((a) => a.model === name);
}
export function auditURL(a: Investigation) {
  return `/registry/${a.model.toLowerCase()}/${a.id}/`;
}
export function figureURL(model: string, variant: string) {
  const record = figures.find(
    (f) => f.model === model && f.version === variant,
  );
  if (!record) throw new Error(`Missing ${variant} figure for ${model}`);
  return "/registry/figures/" + record.file;
}
export function auditMarkdown(a: Investigation): string {
  const showLinks = (links: EvidenceLink[]) =>
    links.map((link) => `- [${link.label}](${link.href})`).join("\n");
  const blocks = [`# ${a.model} — ${a.title}`, `${a.agent} · ${a.date}`];
  for (const text of [a.source, a.date_note, a.eligibility, a.code_provenance]) {
    if (text) blocks.push(text);
  }
  for (const ax of a.axes) {
    blocks.push(
      `## ${ax.name}\n\n${statusNames[ax.status]}. ${ax.result}\n\n**Definition**  \n${ax.definition}\n\n**Data**  \n${ax.data}\n\n**Analysis code**  \n${ax.code}`,
    );
    if (ax.links?.length) blocks.push(showLinks(ax.links));
  }
  blocks.push(
    "## Sources",
    showLinks([
      { label: "Main figure", href: figureURL(a.model, "main") },
      { label: "Expanded figure", href: figureURL(a.model, "expanded") },
      ...a.links,
    ]),
  );
  return blocks.join("\n\n") + "\n";
}
