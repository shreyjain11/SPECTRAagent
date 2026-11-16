# CONCH: individual-entry review

Reviewed all 30 entries, including their Markdown, scientific code and saved outputs. Shared implementations were diffed for every entry; differing candidate branches, eligibility-only entries and confirmation panels were checked separately. There were 237 code cells and 106 numerical/check groups. No neural inference, raw-image feature extraction or bootstrap rerun was performed for this review.

The arithmetic checks use persisted tables at their printed precision: endpoint contrasts, mean class recalls, class eligibility, Spearman correlations, odds-ratio transforms, the tumor pooled contrast and the blur difference-in-differences. The helper `check_conch_entries.py` reproduces these checks.

## Changes made

- Restored missing prose spaces while protecting code fences, inline code, URLs, model names and hashes.
- Scoped Opus r1 sharpness as observational, and its half-split as an internal image-level check.
- Added the fully adjusted CRC uncertainty next to the GPT r2 endpoint decision.
- Removed claims of scoring/checkpoint steps from three unscored input diagnostics.
- Replaced family boilerplate in Kimi r2 stain and site entries with the steps each actually executes.
- Named image-record disjointness and tile-level uncertainty where confirmation could otherwise imply patient/site independence.

This pass changed 73 Markdown cells in 25 notebooks. It changed no code or saved output. Earlier CONCH presentation corrections (CRC class populations and a closing bold marker) remain separately documented under `reproduction/corrections/conch/`. HTML and receipt updates are handled in the parent integration pass.

## Evidence boundaries

- These notebooks are current reconstructions. They do not recover every historical row or establish that the original audit took exactly the same path.
- Fresh CONCH inference needs access approval for the official checkpoint. Public image data alone does not remove this model-access requirement.
- Tile bootstrap intervals do not account for unknown patient/slide clustering. The notebooks do not demonstrate universal cross-site transfer.
- GPT r2 uses 7/9/9/8/9 CRC classes in its plotted curve and seven common endpoint classes in its headline contrast. Both are now labeled.
- Opus r2 currently reconstructs a 0.240741 blur difference-in-differences; the historical report had 0.219. They must not be described as numerically identical.
- GPT r1 test07 retains the exact saved `fixed50-per-level` output and executable source. The HTML now displays `fixed 50-per-level` through a documented whitespace-only presentation correction.

## Entry coverage

| Entry | Evidence checked / interpretation | Limit |
|---|---|---|
| conch-gpt-r1-test-01 | CRC endpoint drop 0.122381; Stanford −0.014493 with an interval crossing zero. Matched CRC drop 0.042056 crosses zero; Stanford reverses to −0.101190. | Matching compares different images within covariate strata, not the same images under an intervention. |
| conch-gpt-r1-test-02 | No model inference. Texture distance is the chosen axis; stain and quality correlations/distributions are measured. | Candidate reattribution, not a negative CONCH performance finding. |
| conch-gpt-r1-test-03 | Shared texture analysis plus tissue fraction by class/level, adjusted coefficients and matching. | A control; no separate independently confirmed tissue-fraction axis. |
| conch-gpt-r1-test-04 | Shared texture analysis plus stain-prototype distance, adjustment and matching. | A control; no separate independently confirmed stain axis. |
| conch-gpt-r1-test-05 | Shared texture analysis plus Laplacian variance, adjustment and focus matching. | Observational image-quality control, not applied blur. |
| conch-gpt-r1-test-06 | Shared texture analysis plus JPEG blockiness and its adjusted coefficient. | A proxy for blockiness, not known compression settings. |
| conch-gpt-r1-test-07 | Recomputed minimum 50 images per class/level retains STR only. No predictions or performance curve. | Limited evaluation eligibility is not a negative model result; Kather and Stanford mappings are separate. |
| conch-gpt-r2-test-01 | Common-class drops: CRC 0.260712 and Stanford 0.043367. Fully adjusted CRC OR 0.901756, CI 0.812564–1.000739, p = 0.051646. | Available-class plotted drop is 0.221537; it differs from the common-seven-class endpoint contrast. |
| conch-gpt-r2-test-02 | Joint-distance curves with stain measurements and adjusted coefficients. | Shared endpoint statistics are not a stain-intervention effect. |
| conch-gpt-r2-test-03 | Joint-distance curves with focus measurements and adjusted coefficients. | No applied blur intervention in this entry. |
| conch-gpt-r2-test-04 | Joint-distance curves with tissue-fraction measurements and adjustment. | No separate confirmed background/tissue effect. |
| conch-gpt-r2-test-05 | Joint-distance curves with JPEG-blockiness measurements and adjustment. | No controlled compression experiment or known compression history. |
| conch-gpt-r2-test-06 | Zero explicit MPP fields in the three cohorts; documented CRC/NCT scale is constant. No model inference. | Missing valid natural-scale variation is not evidence that CONCH is robust to magnification. |
| conch-gpt-r2-test-07 | Same joint-distance association evaluated in Stanford. Site identifies the external panel. | No isolated causal site effect; label mapping and cohort sampling may differ. |
| conch-kimi-r1-test-01 | CONCH drop 68.03 points to factor 16; fixed reference 47.04 points, refitted bank 38.61 points. Class means and contrasts agree. | Controlled downsampling; no acquisition-metadata axis. SSIM covers the first 300 images. |
| conch-kimi-r2-test-01 | CRC drop 0.616820; NCT drop 0.633889. DINO drops 0.216985 and 0.295000; OpenCLIP starts near 0.20 balanced accuracy. | OpenCLIP floor effects limit relative-robustness interpretation; no claim about all scanners. |
| conch-kimi-r2-test-02 | 900-image stain pilot: CONCH drop 0.024444, interval 0.006667–0.042250. Mean LAB change increases to 5.896214. | No NCT confirmation, DINO head or SSIM in this entry; family boilerplate was corrected. |
| conch-kimi-r2-test-03 | Native CONCH balanced accuracy: CRC 0.756350 versus NCT 0.771389; DINO 0.877859 versus 0.968611. | One native level, no degradation contrast and no causal site conclusion. |
| conch-opus-r1-test-01 | Internal-fit novelty OR 0.431987; added pseudo-R² given sharpness 0.002464. A bounded within-class appearance association. | Sharpness is stronger in the joint fit; tissue heterogeneity and internal splitting limit generalization. |
| conch-opus-r1-test-02 | Global novelty/correctness ρ = +0.10392. The decision rejects a uniform pooled decline. | Within-class findings do not rescue the pooled monotonic claim. |
| conch-opus-r1-test-03 | Internal-fit sharpness OR 9.443469; added pseudo-R² given novelty 0.020969. | Natural sharpness association; corrected prose does not call this a controlled corruption experiment. |
| conch-opus-r2-test-01 | Target drop 0.53796296; reference drop 0.29722222; difference 0.24074074, paired interval 0.20092593–0.28055556. | Current reconstruction differs from historical DiD 0.219; confirmation concerns different image records. |
| conch-opus-r2-test-02 | Twelve-feature development screen; within-class hematoxylin correlation −0.087221. No separately confirmed stain curve. | Blur confirmation cannot confirm a stain result. |
| conch-opus-r2-test-03 | Marginal associations change after class control. The blur panel holds every image and all nine class counts fixed. | Composition diagnostic, not another independently confirmed axis. |
| conch-primary-test-01 | Raw ρ = −0.485714; fixed-class ρ = +0.828571. The decision correctly withholds a monotone model-specific decline. | Six fixed classes; changing tissue mixtures prevent relying on the pooled curve alone. |
| conch-primary-test-02 | Raw ρ = −0.085714; fixed-five-class ρ = −0.942857. Kept as a secondary screen without separate confirmation. | Within-class degradation does not establish an independently confirmed color boundary. |
| conch-primary-test-03 | Raw ρ = −0.771429; only ADI meets support at every level, with ρ = −0.492805. Kept as a secondary screen. | Only one class supports the fixed-population comparison. |
| conch-primary-test-04 | 1,800 confirmation and 4,000 expansion tiles. Main pooled drop 0.24952381, normal interval 0.22072297–0.27832464. | Localized tumor-tail finding in one source family; patient/slide independence is unverified. |
| conch-primary-test-05 | Joint-axis fixed-class direction reverses the pooled direction. The decision identifies composition confounding. | Shares predictions and curves with test 01; not a separate failure axis. |
| conch-primary-test-06 | Overall balanced accuracy: CONCH 0.756350, nearest centroid 0.602062, logistic 0.618660. References trained on NCT only. | Overall accuracy alone does not establish model-specific degradation; per-level reference curves are the relevant controls. |

Full per-cell source/output hashes, precise changed Markdown and numerical checks are in `conch-entry-review.json`. This report does not claim independent execution of the GPU analyses.
