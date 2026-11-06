import { readFileSync } from "node:fs";
import { join } from "node:path";
import { notebookFile, type Investigation } from "./paper-registry";
import { validateNotebookMetadata } from "./notebook-metadata.mjs";

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
  cell_type: string;
  source: string | string[];
  metadata: { spectra_role?: string; filename?: string; title?: string };
  execution_count?: number;
  outputs?: CellOutput[];
};
type Notebook = {
  nbformat: number;
  metadata: { spectra: {
    auditId: string; axis: number; name: string; note: string;
    kind: "curve" | "comparison" | "table" | "analysis" | "none";
    bundleUrl?: string;
    reproducibility?: {
      end_to_end: boolean;
      stages: { id: "dataset" | "axis" | "evaluation" | "curve" | "insight"; label: string; status: string; detail: string }[];
      missing: string[];
    };
  } };
  cells: Cell[];
};

export const textOf = (value?: string | string[]) =>
  Array.isArray(value) ? value.join("") : (value || "");

export function readNotebook(audit: Investigation, index: number) {
  const path = join(process.env.SPECTRA_REGISTRY_BUNDLE!, "public", notebookFile(audit, index));
  const book: Notebook = JSON.parse(readFileSync(path, "utf8"));
  const info = book.metadata?.spectra;
  validateNotebookMetadata(info, {
    context: path,
    requireCoverage: process.env.SPECTRA_REQUIRE_REPRODUCIBILITY === "1",
  });
  if (book.nbformat !== 4 || info.auditId !== audit.id || info.axis !== index + 1 ||
      info.name !== audit.axes[index].name) {
    throw new Error("Notebook does not match the audit test: " + path);
  }
  return book;
}
