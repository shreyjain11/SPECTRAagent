export const reproductionStageIds = ["dataset", "axis", "evaluation", "curve", "insight"];

/** Validate supplied coverage without interpreting its scientific claims. */
export function validateNotebookMetadata(meta, { context = "Notebook", requireCoverage = false } = {}) {
  const check = (condition, message) => {
    if (!condition) throw new Error(`${context}: ${message}`);
  };
  const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const text = (value, max = 20000) => typeof value === "string" && value.trim().length > 0 && value.length <= max;

  check(object(meta), "metadata.spectra must be an object");
  if (meta.bundleUrl !== undefined) {
    check(text(meta.bundleUrl, 2048), "bundleUrl must be a nonempty URL");
    const url = new URL(meta.bundleUrl, "https://registry.invalid");
    const local = meta.bundleUrl.startsWith("/") && !meta.bundleUrl.startsWith("//");
    check((local || meta.bundleUrl.startsWith("https://")) && !/[\\\s]/.test(meta.bundleUrl),
      "bundleUrl must be a site-relative path or HTTPS URL");
    check(!url.username && !url.password && !url.hash, "bundleUrl must not contain credentials or a fragment");
    if (local) {
      check(url.origin === "https://registry.invalid", "bundleUrl must stay on the site");
      check(!url.pathname.split("/").some((part) => /[\\/]/.test(decodeURIComponent(part))) &&
        !meta.bundleUrl.split(/[/?#]/).some((part) => [".", ".."].includes(decodeURIComponent(part))),
        "bundleUrl must not contain path traversal or encoded path separators");
    }
  }

  const coverage = meta.reproducibility;
  if (coverage === undefined) {
    check(!requireCoverage, "metadata.spectra.reproducibility is required");
    return;
  }
  check(object(coverage), "reproducibility must be an object");
  check(typeof coverage.end_to_end === "boolean", "reproducibility.end_to_end must be a boolean");
  check(Array.isArray(coverage.stages) && coverage.stages.length === reproductionStageIds.length,
    "reproducibility.stages must contain all five stages");
  for (const [index, id] of reproductionStageIds.entries()) {
    const stage = coverage.stages[index];
    check(object(stage) && stage.id === id, `reproducibility.stages[${index}] must identify ${id}`);
    check(text(stage.label, 200), `${id}.label must be nonempty text (up to 200 characters)`);
    check(text(stage.status, 160), `${id}.status must be nonempty text (up to 160 characters)`);
    check(text(stage.detail), `${id}.detail must be nonempty text`);
  }
  check(Array.isArray(coverage.missing) && coverage.missing.every((item) => text(item)),
    "reproducibility.missing must be an array of nonempty descriptions");
  check(!coverage.end_to_end || coverage.missing.length === 0,
    "end_to_end cannot be true while limits or missing inputs are listed");
}
