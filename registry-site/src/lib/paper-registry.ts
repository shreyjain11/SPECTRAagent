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
  explanation: string;
  data: string;
  code: string;
  result: string;
  review_note?: string;
  links?: EvidenceLink[];
};
export type Investigation = {
  id: string;
  model: string;
  title: string;
  summary: string;
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
    description: "Predicts a protein’s three-dimensional structure from its amino-acid sequence. The audits examine which kinds of proteins are harder to predict accurately.",
  },
  {
    slug: "state",
    name: "STATE",
    figure: 3,
    field: "Perturbation biology",
    task: "Gene-expression response to genetic or chemical perturbations.",
    description: "Predicts how a cell’s gene activity changes after a gene is disrupted or a drug is applied. The audits test performance across cell types, treatments and examples with different amounts of training support.",
  },
  {
    slug: "conch",
    name: "CONCH",
    figure: 4,
    field: "Computational pathology",
    task: "Zero-shot classification of colorectal tissue images.",
    description: "Matches tissue images to text descriptions to identify tissue types. These audits test whether image appearance, focus and resolution affect its accuracy on colorectal tissue.",
  },
  {
    slug: "alphamissense",
    name: "AlphaMissense",
    figure: 5,
    field: "Variant effects",
    task: "Missense variant pathogenicity and functional effects.",
    description: "Estimates whether changing one amino acid in a human protein is harmful. The audits compare its scores with clinical labels and laboratory measurements across different kinds of variants.",
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
export function notebookURL(audit: Investigation, index: number) {
  return auditURL(audit) + "notebook-" + (index + 1) + "/";
}
export function notebookFile(audit: Investigation, index: number) {
  const number = String(index + 1).padStart(2, "0");
  return `/registry/notebooks/${audit.id}/test-${number}.ipynb`;
}
export function figureURL(model: string, variant: string) {
  const record = figures.find(
    (f) => f.model === model && f.version === variant,
  );
  if (!record) throw new Error(`Missing ${variant} figure for ${model}`);
  return "/registry/figures/" + record.file;
}
export function auditMarkdown(a: Investigation): string {
  const blocks = [`# ${a.model} — ${a.title}`, `${a.agent} · ${a.date}`, a.summary];
  for (const text of [a.date_note, a.eligibility]) {
    if (text) blocks.push(text);
  }
  for (const [index, ax] of a.axes.entries()) {
    blocks.push(
      `## ${ax.name}\n\n${ax.explanation}\n\n${statusNames[ax.status]}. ${ax.result}` +
      (ax.review_note ? `\n\nReproduction review: ${ax.review_note}` : "") +
      `\n\n[Measurements, data and code](${notebookURL(a, index)})`,
    );
  }
  return blocks.join("\n\n") + "\n";
}
