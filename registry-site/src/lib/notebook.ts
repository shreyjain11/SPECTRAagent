import { readFileSync } from "node:fs";
import { join } from "node:path";
import { notebookFile, type Investigation } from "./paper-registry";

export type Table = { headers: string[]; rows: string[][] };
type CellOutput = {
  output_type: string;
  text?: string | string[];
  data?: {
    "image/png"?: string;
    "text/plain"?: string | string[];
    "application/vnd.spectra.table+json"?: Table;
  };
};
type Cell = {
  source: string | string[];
  metadata: { spectra_role: string; filename?: string };
  execution_count?: number;
  outputs?: CellOutput[];
};
type Notebook = {
  nbformat: number;
  metadata: { spectra: { auditId: string; axis: number; name: string; note: string; kind: string } };
  cells: Cell[];
};

export const textOf = (value?: string | string[]) =>
  Array.isArray(value) ? value.join("") : (value || "");

export function readNotebook(audit: Investigation, index: number) {
  const path = join(process.env.SPECTRA_REGISTRY_BUNDLE!, "public", notebookFile(audit, index));
  const book: Notebook = JSON.parse(readFileSync(path, "utf8"));
  const info = book.metadata.spectra;
  if (book.nbformat !== 4 || info.auditId !== audit.id || info.axis !== index + 1 ||
      info.name !== audit.axes[index].name) {
    throw new Error("Notebook does not match the audit test: " + path);
  }
  return book;
}
