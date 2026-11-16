"""Apply the prose corrections from the individual ESMFold notebook review.

Scientific code and saved outputs are deliberately preserved. These notes are
an interpretation of the displayed calculations, not a new execution.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = {
    'esmfold2-featured': [
        'The displayed result is a localized low-support association in the CAMEO panel: the high-minus-low support difference is 0.1956 C-alpha lDDT. Alignment depth is a measured support proxy; these data do not identify the model’s exact training-set membership or establish a universal degradation law.',
        'CAMEO difficulty is associated with lower accuracy in this panel. The length association points in the opposite direction to a longer-chain failure, and the resolution rank test is inconclusive. These observational controls do not establish causation.',
        'The 107-target follow-up does not confirm the proposed flexible/non-helical decline: the primary top-minus-lower estimate is +0.0311 C-alpha lDDT, with a bootstrap interval spanning zero. Earlier screening curves and oracle sample selection do not override that follow-up result.',
        'The charge follow-up does not confirm a decline: the primary top-minus-lower estimate is +0.0069 C-alpha lDDT, with a bootstrap interval spanning zero. This concerns absolute sequence charge; it is distinct from the signed-charge cryo-EM comparison in Codex r2.',
        'The acidic-window follow-up has 77 finite results from 78 targets. Its primary top-minus-lower estimate is −0.0173 C-alpha lDDT, with a 95% bootstrap interval of [−0.0803, 0.0318]. The adjusted coefficient is negative, but the primary endpoint contrast remains unresolved. The generic direction labels below are descriptive and do not establish confirmation.',
        'The cysteine follow-up has 93 finite results from the 95-target panel, including 17 in the high group. Its primary top-minus-lower estimate is −0.0943 C-alpha lDDT, with an interval of [−0.2003, −0.0017]. This supports a cohort-specific association; cysteine fraction alone does not identify actual disulfide bonds or a universal mechanism.',
        'These pooled screens compare several sequence and protein-description subsets. Their pointwise intervals do not by themselves establish an independently confirmed viral-envelope effect. The separate pilot, envelope and surface-panel analyses are reported in tests 10–12.',
        'Potential disulfide capacity is a sequence proxy based on cysteine pairs, not a measurement of formed disulfide bonds. The displayed pooled and subtype screens are descriptive; the combined viral/disulfide pilot is evaluated separately in test 10.',
        'These geometry features are computed from experimental reference structures. They are retrospective structure-based diagnostics, not properties available from a sequence-only query. A declining endpoint in the summary table is not itself a confirmed prospective failure axis.',
        'The pilot includes only eight targets in the combined high regime. Its −0.0922 C-alpha lDDT contrast has a 95% interval of [−0.2799, 0.0562], so the direction is suggestive and the contrast is unresolved.',
        'The prespecified envelope/fusion proxy is unresolved in the 38-target panel: −0.0149 C-alpha lDDT, with an interval spanning zero. The 16 additional candidate contrasts use this same panel and are exploratory; their pointwise intervals are not independent confirmation.',
        'The broad surface regime is unresolved: +0.0219 C-alpha lDDT with an interval spanning zero. The class-II E/E2 subset has eight targets and a negative contrast (−0.2301; interval [−0.3073, −0.1535]). That narrower subtype contrast does not validate the broad regime, and the name-defined subtypes remain subject to the stated selection scope.',
    ],
    'esmfold2-codex-r1': [
        'The current reconstruction evaluates 1,987 primary-axis chains and 530 auxiliary controls. The extreme-level model decline is 0.0953 TM-score; the template decline is larger (0.4858). This is a cohort association with shared difficulty under that comparator, not excess ESMFold2 degradation or recovery of the exact historical cohort. Some adjustment designs are rank deficient; aliased nuisance coefficients should not receive separate biological interpretations.',
        'Length and homology are covariate and reference checks on the same reconstructed population. Their displayed curves are not independent replications of the Pfam result. The template comparison uses the available pre-cutoff reference and its stated abstention handling.',
        'Disorder and coiled-coil burden have negative conditional coefficients in this population. Failing to remove the primary Pfam contrast does not mean these features have no association with accuracy. These are same-cohort controls, not separate confirmed failure-axis tests.',
        'This entry documents an unperformed membrane candidate. It contains no membrane-axis model evaluation and supports no positive or negative performance claim.',
    ],
    'esmfold2-codex-r2': [
        'In the fixed 150-chain cohort, the negative-to-positive charge contrast is a 0.1006 TM-score decline. The model-minus-template decline is −0.0130 with a 95% interval of [−0.1197, 0.0928]. Thus the measured decline is supported, but greater model-specific degradation or statistical equivalence to the reference is not established.',
        'The 120-target repeat panel has a model endpoint decline of only 0.0037 TM-score, with an interval spanning zero and non-monotone adjusted means. It does not confirm the proposed repeat weakness; it does not establish robustness to every form of repetition.',
        'The 240-target entropy panel has a high-risk-minus-low-risk difference of +0.00295 TM-score, with an interval spanning zero. The template reference declines more, but that comparison is not evidence of an ESMFold2 entropy failure. The 40/60/80-per-level summaries are nested subsets, not independent replications.',
        'The 147-target multiplicity panel has a 0.0292 TM-score endpoint decline, with an interval spanning zero. Entity copy count is an experimental-structure context proxy; it is not a direct intervention on the model input or proof of a biological oligomerization effect.',
        'The 240-target dominant-residue panel has a high-risk-minus-low-risk difference of +0.00853 TM-score, with an interval spanning zero. It does not confirm the proposed weakness in this selected panel.',
        'The 45-target screen assigns candidate direction labels from correlation signs. A direction label is not a significance test or confirmation. The same discovery outcomes are used to screen multiple features; subsequent confirmation panels must be interpreted separately.',
    ],
    'esmfold2-opus-r1': [
        'On the current confirmation split, lower homology support is associated with lower fixed-correspondence TM-score (low-minus-high −0.083, interval [−0.121, −0.045]). The matched AlphaFold comparison supports a larger ESMFold2 drop on covered examples. This is relative to that particular reference and cohort, not a claim about every comparator or exact replay of the historical run.',
        'The confirmation length association is positive after covariate adjustment, opposite to the proposed longer-chain decline. The negative low-minus-high contrast means shorter chains scored worse here; it is not evidence for a longer-chain failure.',
        'The confirmation disorder association is negative after covariate adjustment, and the low-minus-high disorder contrast is positive (0.062; interval [0.024, 0.102]). This supports a cohort association with the sequence-derived FoldIndex proxy, not a causal effect of experimentally measured disorder.',
        'These six controls are evaluated on the same confirmation cohort. The displayed Bonferroni column adjusts this control family for multiplicity; the other notebooks’ “adjusted” correlations refer to covariate adjustment. The controls do not create six independent causal failure axes.',
    ],
    'esmfold2-opus-r2': [
        'Of 401 supplied identifiers, 400 are evaluated and 384 lie in the primary length range. The adjusted length coefficient is positive and unresolved at p < 0.05; the level means are non-monotone. This does not support a general longer-chain decline. Model and template curve means use different coverage counts; matched-reference analyses are reported separately.',
        'The reference is the pre-cutoff public PDB pool, not a verified manifest of training examples. The adjusted identity coefficient is near zero and unresolved. Template coverage is only 25 of 63 targets in the lowest-identity primary bin, so unpaired curve means do not describe identical target populations.',
        'The displayed tail fractions vary by length, but the long-arm model failure trend is unresolved (p = 0.3973). The 16-target longest bin is exploratory. A few low-scoring tails do not establish a monotone longer-chain failure.',
        'Resolution and copy count have nominal adjusted associations; the entropy coefficient is unresolved. These are observational covariate checks in the same panel. The printed p < 0.05 labels are nominal and do not by themselves account for testing multiple features.',
    ],
    'esmfold2-kimi-r1': [
        'These are ESMFold v1 predictions, not ESMFold2 predictions. The four means are not monotone and the endpoint difference (0.0806) is below the stated 0.15 threshold, despite the small trend p-value. Reference coverage falls to 10 of 80 targets in the lowest-support group.',
        'These are ESMFold v1 predictions. The binary non-orphan-minus-orphan difference is 0.0862 TM-score and remains positive in all three length strata. Only 27 of 170 orphans have a template reference, so the pooled model drop cannot establish a matched model-specific effect across the full orphan cohort.',
        'These are ESMFold v1 predictions. The highest low-complexity level has only 16 targets, and its mean score is higher rather than lower than the first level. This remains an exploratory, underfilled comparison and is not an ESMFold2 result.',
    ],
    'esmfold2-kimi-r2': [
        'The pooled 160-target endpoint is significant (0.0861 TM-score; p = 0.0299), but the 128-target expansion does not independently confirm it (0.0598; p = 0.1468). The level means are non-monotone. No template is available in the lowest-identity bin, so a four-level matched degradation comparison is unavailable.',
        'These are sensitivity analyses of the same 160 targets, not additional independent cohorts. The observed-fraction-only restriction has an unresolved endpoint, while the single-entity and combined restrictions retain an endpoint difference. The expansion remains inconclusive and lowest-bin template coverage is absent.',
    ],
}

# Words checked in the prose, not a general letter-digit substitution: biological
# names, identifiers, URLs, software commands and hashes remain intact.
WORDS = 'and seed are with least Transformers length through at resolution use sensitivity before released than Bootstrap coverage to levels the uses commit bidirectional require precede exact separations score displays of maximum density proxy specifies after by November September October June request plus over Require metapredict disorder NCOILS probability TANTAN receives distances Use above The year all most Construct from mode unique disjoint Calculate Acquire chains per capacity triplets including fraction Scan entropy'.split()
PATTERN = re.compile(r'\b(' + '|'.join(sorted(WORDS, key=len, reverse=True)) + r')(?=[0-9≤≥<>])')
PROTECTED = re.compile(r'(```[\s\S]*?```|`[^`]*`|https?://[^\s)]+)')

def prose_spacing(s):
    parts = PROTECTED.split(s)
    for i in range(0, len(parts), 2):
        t = PATTERN.sub(r'\1 ', parts[i])
        t = re.sub(r'(?<=\d)Å', ' Å', t)
        t = re.sub(r'(?<=[,;])(?=\d)', ' ', t)
        t = t.replace('Charge is((', 'Charge is ((').replace('the−0.09', 'the −0.09')
        parts[i] = t
    return ''.join(parts)

def main():
    ledger = []
    for group, notes in NOTES.items():
        for number, note in enumerate(notes, 1):
            identifier = f'{group}/test-{number:02d}'
            path = ROOT / 'inline/esmfold2' / (identifier + '.ipynb')
            book = json.loads(path.read_text())
            changed = []
            for i, cell in enumerate(book['cells']):
                if cell['cell_type'] != 'markdown':
                    continue
                old = ''.join(cell['source'])
                new = prose_spacing(old)
                if re.match(r'^## 6[.)]', new):
                    new = new.rstrip() + '\n\n' + note + '\n'
                if new != old:
                    cell['source'] = new.splitlines(keepends=True)
                    changed.append({'cell': i, 'before': old, 'after': new})
            if group == 'esmfold2-opus-r1':
                c = book['cells'][17]
                s = ''.join(c['source']).replace('an adjusted p-value below 0.05', 'a covariate-adjusted p-value below 0.05')
                c['source'] = s.splitlines(keepends=True)
            path.write_text(json.dumps(book, ensure_ascii=False, indent=1) + '\n')
            code = [c for c in book['cells'] if c['cell_type'] == 'code']
            ledger.append({'id': identifier, 'review_scope': 'Individual prose, saved result tables and decision logic reviewed; common acquisition, scoring and aggregation functions inspected across the family. No fresh model inference.', 'evidence_checked': ['dataset and split description', 'axis and level code', 'model/version and score source', 'reported curve and uncertainty', 'conclusion relative to displayed controls and confirmation'], 'interpretation': note, 'code_cells': len(code), 'markdown_changes': changed, 'numerical_reexecution_in_this_review': False, 'remaining_limits': ['Current reconstruction is not assumed identical to the original historical audit.', 'Execution evidence does not independently validate every upstream prediction.']})
    (Path(__file__).parent / 'esmfold2-entry-review.json').write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + '\n')
    print(f'Reviewed and annotated {len(ledger)} ESMFold entries; code and outputs unchanged.')

if __name__ == '__main__':
    main()
