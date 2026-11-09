# Step B — Axis-3 AM scoring results (Path A, occupancy axis)

**Date:** 2026-06-10. AM AlphaMissense_aa_substitutions.tsv.gz joined to ProteinGym v1.3 DMS single mutants (73 assays). Bins FROZEN before scoring (`stepB/axis3_pathC_percolumn_FROZEN.tsv`). Accuracy metric = **|Spearman(AM, DMS_score)|** per (assay,bin); aggregated across assays. `wmean` = variant-count-weighted mean |rho|; `umean` = unweighted mean; `median` = median. Min variants/(assay,bin) = 20.

## 0. Join coverage

- Total single mutants (no-colon) across 73 assays: **273135**
- AM-scored: **270572** (99.1%)
- AM-scored AND within a frozen occupancy bin (usable for SPC): **270572**
- Overall |Spearman| (all binned variants, no split): wmean=0.482 over 72 assays / 63 proteins / 270572 variants

### Assays with <90% AM join coverage
| assay | acc | n_single | n_scored | cov | offfail | wt_mismatch | no_AM_var | status |
|---|---|---|---|---|---|---|---|---|
| UBC9_HUMAN_Weile_2017 | P63279 | 2563 | 0 | 0% | 2563 | 0 | 0 | OFFSET_FAIL |

## 1. Coarse headline — hard vs easy (occupancy)

Hard = insert-state OR aligned occ≤0.9 ; Easy = aligned occ>0.9.

| bin | n_assays | n_proteins | n_variants | wmean \|rho\| | umean | median |
|---|---|---|---|---|---|---|
| HARD (insert + occ≤0.9) | 65 | 56 | 63148 | 0.349 | 0.357 | 0.355 |
| EASY (occ>0.9) | 68 | 59 | 207424 | 0.476 | 0.472 | 0.475 |

**Hard-vs-easy gap (easy_wmean − hard_wmean) = +0.128**  (positive = AM less accurate on hard columns).

## 2. Quintile resolution — 5 occupancy bins (aligned) + insert-state

| occ bin | range | n_assays | n_proteins | n_variants | wmean \|rho\| | umean | median |
|---|---|---|---|---|---|---|---|
| q0 | occ≤0.945 | 62 | 53 | 45606 | 0.395 | 0.387 | 0.421 |
| q1 | 0.945–0.987 | 61 | 53 | 49852 | 0.418 | 0.433 | 0.446 |
| q2 | 0.987–0.998 | 62 | 54 | 57338 | 0.443 | 0.448 | 0.465 |
| q3 | 0.998–0.999 | 56 | 49 | 26849 | 0.506 | 0.511 | 0.517 |
| q4 | occ>0.999 (~1.0) | 60 | 53 | 59838 | 0.515 | 0.493 | 0.523 |
| insert-state (hardest) | 48 | 44 | 30910 | 0.266 | 0.297 | 0.270 |

## 3. Interaction — deep (Neff≥200) AND low-occupancy vs deep high-occupancy

Tests 'hard-to-align ≠ shallow': among columns with abundant homologs, does gappiness still degrade AM?

| cell | n_assays | n_proteins | n_variants | wmean \|rho\| | umean | median |
|---|---|---|---|---|---|---|
| DEEP & occ<0.5 | 19 | 17 | 2342 | 0.386 | 0.342 | 0.265 |
| DEEP & occ<0.7 | 28 | 25 | 5438 | 0.305 | 0.286 | 0.305 |
| DEEP & occ≥0.9 (reference) | 58 | 50 | 192059 | 0.475 | 0.480 | 0.489 |

**Interaction gap (deep-high − deep&occ<0.7) = +0.169**

## 4. Per-assay |rho| for the coarse split (transparency)

| assay | acc | n_hard | rho_hard | n_easy | rho_easy |
|---|---|---|---|---|---|
| A4_HUMAN_Seuma_2022 | P05067 | 796 | -0.495 | 0 | nan |
| ACE2_HUMAN_Chan_2020 | Q9BYF1 | 38 | 0.281 | 2185 | -0.245 |
| ADRB2_HUMAN_Jones_2020 | P07550 | 2737 | -0.121 | 5063 | -0.576 |
| AICDA_HUMAN_Gajula_2014_3cycles | Q9GZX7 | 76 | -0.163 | 133 | -0.499 |
| B2L11_HUMAN_Dutta_2010_binding-Mcl-1 | O43521 | 0 | nan | 170 | -0.417 |
| BRCA1_HUMAN_Findlay_2018 | P38398 | 1510 | -0.584 | 327 | -0.516 |
| BRCA2_HUMAN_Erwood_2022_HEK293T | P51587 | 0 | nan | 265 | -0.433 |
| CALM1_HUMAN_Weile_2017 | P0DP23 | 576 | -0.213 | 1237 | -0.196 |
| CAR11_HUMAN_Meitlis_2020_gof | Q9BXL7 | 227 | -0.007 | 2147 | -0.199 |
| CAR11_HUMAN_Meitlis_2020_lof | Q9BXL7 | 228 | -0.150 | 2167 | -0.344 |
| CBPA2_HUMAN_Tsuboyama_2023_1O6X | P48052 | 170 | 0.201 | 1187 | -0.473 |
| CBS_HUMAN_Sun_2020 | P35520 | 1454 | -0.151 | 5763 | -0.419 |
| CBX4_HUMAN_Tsuboyama_2023_2K28 | O00257 | 339 | -0.503 | 578 | -0.355 |
| CCR5_HUMAN_Gill_2023 | P51681 | 1482 | -0.087 | 4655 | -0.362 |
| CD19_HUMAN_Klesmith_2019_FMC_singles | P15391 | 756 | -0.212 | 3005 | -0.291 |
| CP2C9_HUMAN_Amorosi_2021_abundance | P11712 | 1501 | -0.584 | 4869 | -0.596 |
| CP2C9_HUMAN_Amorosi_2021_activity | P11712 | 1488 | -0.556 | 4654 | -0.649 |
| DLG4_HUMAN_Faure_2021 | P78352 | 47 | -0.569 | 1233 | -0.448 |
| DNJA1_HUMAN_Tsuboyama_2023_2LO1 | P31689 | 112 | 0.495 | 1104 | -0.306 |
| EPHB2_HUMAN_Tsuboyama_2023_1F0M | P29323 | 242 | -0.552 | 997 | -0.569 |
| ERBB2_HUMAN_Elazar_2016 | P04626 | 0 | nan | 326 | -0.459 |
| FKBP3_HUMAN_Tsuboyama_2023_2KFV | Q00688 | 171 | -0.608 | 1066 | -0.415 |
| GDIA_HUMAN_Silverstein_2021 | P31150 | 91 | -0.644 | 1063 | -0.450 |
| GRB2_HUMAN_Faure_2021 | P62993 | 1034 | -0.553 | 0 | nan |
| HEM3_HUMAN_Loggerenberg_2023 | P08397 | 891 | -0.170 | 4798 | -0.504 |
| HMDH_HUMAN_Jiang_2019 | P04035 | 2128 | 0.075 | 14725 | -0.401 |
| HXK4_HUMAN_Gersing_2022_activity | P35557 | 783 | -0.075 | 7787 | -0.534 |
| HXK4_HUMAN_Gersing_2023_abundance | P35557 | 784 | -0.194 | 7612 | -0.398 |
| KCNH2_HUMAN_Kozek_2020 | Q12809 | 0 | nan | 200 | -0.464 |
| LYAM1_HUMAN_Elazar_2016 | P14151 | 359 | -0.355 | 0 | nan |
| MET_HUMAN_Estevam_2023 | P08581 | 583 | -0.292 | 4810 | -0.618 |
| MK01_HUMAN_Brenan_2016 | P28482 | 1668 | 0.018 | 5141 | -0.233 |
| MSH2_HUMAN_Jia_2020 | P43246 | 3041 | -0.130 | 13708 | -0.448 |
| MTHR_HUMAN_Weile_2021 | P42898 | 1843 | -0.224 | 10621 | -0.292 |
| NPC1_HUMAN_Erwood_2022_HEK293T | O15118 | 87 | -0.553 | 550 | -0.720 |
| NPC1_HUMAN_Erwood_2022_RPE1 | O15118 | 35 | -0.615 | 28 | -0.885 |
| NUD15_HUMAN_Suiter_2020 | Q9NV35 | 1106 | -0.528 | 1738 | -0.690 |
| OBSCN_HUMAN_Tsuboyama_2023_1V1C | Q5VST9 | 337 | -0.176 | 876 | -0.574 |
| OPSD_HUMAN_Wan_2019 | P08100 | 42 | -0.690 | 123 | -0.533 |
| OTC_HUMAN_Lo_2023 | P00480 | 209 | -0.808 | 1361 | -0.546 |
| OTU7A_HUMAN_Tsuboyama_2023_2L2D | Q8TE49 | 198 | -0.124 | 437 | -0.221 |
| P53_HUMAN_Kotler_2018 | P04637 | 0 | nan | 1048 | -0.707 |
| PAI1_HUMAN_Huttinger_2021 | P05121 | 465 | -0.241 | 4880 | -0.393 |
| PIN1_HUMAN_Tsuboyama_2023_1I6C | Q13526 | 222 | -0.447 | 464 | -0.577 |
| PPARG_HUMAN_Majithia_2016 | P37231 | 3686 | -0.371 | 5890 | -0.542 |
| PPM1D_HUMAN_Miller_2022 | O15297 | 4188 | -0.517 | 3701 | -0.693 |
| PR40A_HUMAN_Tsuboyama_2023_1UZC | O75400 | 299 | -0.475 | 864 | -0.506 |
| PRKN_HUMAN_Clausen_2023 | O60260 | 1614 | -0.544 | 7142 | -0.651 |
| PTEN_HUMAN_Matreyek_2021 | P60484 | 1565 | -0.240 | 3518 | -0.473 |
| PTEN_HUMAN_Mighell_2018 | P60484 | 2125 | -0.256 | 5135 | -0.594 |
| RAF1_HUMAN_Zinkus-Boltz_2019 | P04049 | 297 | -0.496 | 0 | nan |
| RASH_HUMAN_Bandaru_2017 | P01112 | 227 | -0.183 | 2907 | -0.471 |
| RD23A_HUMAN_Tsuboyama_2023_1IFY | P54725 | 224 | -0.587 | 574 | -0.553 |
| S22A1_HUMAN_Yee_2023_abundance | O15245 | 3529 | -0.616 | 6274 | -0.596 |
| S22A1_HUMAN_Yee_2023_activity | O15245 | 3546 | -0.586 | 6548 | -0.610 |
| SC6A4_HUMAN_Young_2021 | P31645 | 2942 | -0.336 | 8634 | -0.478 |
| SCN5A_HUMAN_Glazer_2019 | Q14524 | 0 | nan | 224 | -0.210 |
| SERC_HUMAN_Xie_2023 | Q9Y617 | 356 | -0.425 | 1558 | -0.587 |
| SHOC2_HUMAN_Kwon_2022 | Q9UQ13 | 3836 | -0.343 | 7136 | -0.519 |
| SOX30_HUMAN_Tsuboyama_2023_7JJK | O94993 | 152 | 0.143 | 858 | -0.273 |
| SRC_HUMAN_Ahler_2019 | P12931 | 20 | -0.448 | 3352 | -0.580 |
| SRC_HUMAN_Chakraborty_2023_binding-DAS_25uM | P12931 | 22 | -0.536 | 3615 | -0.509 |
| SRC_HUMAN_Nguyen_2022 | P12931 | 20 | -0.361 | 3346 | -0.514 |
| SUMO1_HUMAN_Weile_2017 | P63165 | 474 | -0.326 | 1226 | -0.521 |
| TADBP_HUMAN_Bolognesi_2019 | Q13148 | 558 | 0.076 | 638 | 0.077 |
| TPK1_HUMAN_Weile_2017 | Q9H3S4 | 1069 | -0.301 | 2112 | -0.311 |
| TPMT_HUMAN_Matreyek_2018 | P51580 | 1198 | -0.405 | 2450 | -0.589 |
| UBE4B_HUMAN_Tsuboyama_2023_3L1X | O95155 | 341 | -0.379 | 777 | -0.416 |
| UBR5_HUMAN_Tsuboyama_2023_1I2T | O95071 | 93 | -0.293 | 1001 | -0.444 |
| VKOR1_HUMAN_Chiasson_2020_abundance | Q9BQB6 | 731 | -0.468 | 1964 | -0.442 |
| VKOR1_HUMAN_Chiasson_2020_activity | Q9BQB6 | 180 | -0.061 | 517 | -0.463 |
| YAP1_HUMAN_Araya_2012 | P46937 | 0 | nan | 362 | -0.507 |

## 5. Paired within-assay significance (sign test, delta = clean − hard, |rho|)

Controls for assay-level baseline differences: each assay contributes one paired delta.

| comparison | n_pairs | clean>hard | median Δ | mean Δ | sign-test p |
|---|---|---|---|---|---|
| coarse easy − hard | 61 | 47/61 | +0.152 | +0.124 | 2.72e-05 |
| easy − insert-state | 46 | 38/46 | +0.188 | +0.181 | 9.25e-06 |
| q4(clean) − q0(gappy) | 53 | 44/53 | +0.088 | +0.112 | 1.22e-06 |
| DEEP: occ≥0.9 − occ<0.7 | 28 | 24/28 | +0.216 | +0.202 | 1.80e-04 |
| DEEP: occ≥0.9 − occ<0.5 | 19 | 12/19 | +0.254 | +0.152 | 3.59e-01 |

**Read:** coarse, insert, quintile, and the deep&occ<0.7 interaction are all significant (p≤2e-4) and consistently ordered. The extreme deep&occ<0.5 cell is underpowered (n=19) and non-monotone vs occ<0.7 → treat as noise, not a reversal; the robust deep-gappy signal is the occ<0.7 band.


## 6. Sign-aware gap (supplement) -- anti-correlation scored as 0

Correct direction per assay = sign of its easy-bin (occ>0.9) signed rho. A (assay,bin) that predicts in the WRONG direction contributes 0 instead of |rho|. This removes the |rho| reward for backwards prediction; the gap widens, confirming |rho| is conservative.

| comparison | |rho| gap | sign-aware gap |
|---|---|---|
| coarse easy − hard | +0.128 | +0.133 |
| DEEP occ≥0.9 − occ<0.7 | +0.169 | +0.179 |

(coarse: easy |rho|=0.476/sign-aware=0.476; hard |rho|=0.349/sign-aware=0.344. DEEP: clean |rho|=0.475/sign-aware=0.475; gappy |rho|=0.305/sign-aware=0.296.)



## 7. AM-independent baselines + DMS-signal control (figure v2)

Two baselines scored on the IDENTICAL frozen bins: theta=0.2-weighted site-independent PSSM log-odds (uses MSA column) and BLOSUM62 (position/MSA-blind, substitution type only). Metric = per-assay |Spearman|, variant-weighted, 5,000-resample bootstrap CI over assays.

| bin | AM | PSSM | BLOSUM62 |
|---|---|---|---|
| insert | 0.266 | — | 0.119 |
| q0 | 0.395 | 0.308 | 0.157 |
| q1 | 0.418 | 0.372 | 0.196 |
| q2 | 0.443 | 0.410 | 0.221 |
| q3 | 0.506 | 0.432 | 0.230 |
| q4 | 0.515 | 0.479 | 0.244 |
| deep_occ>=0.9 | 0.475 | 0.434 | 0.213 |
| deep_occ<0.7 | 0.305 | 0.274 | 0.153 |

**DMS-signal control — within-assay DMS spread per bin (normalised to each assay's overall):**

| bin | median within-assay DMS std | mean relative spread | n_assays |
|---|---|---|---|
| insert | 0.414 | 0.730 | 48 |
| q0 | 0.518 | 0.865 | 62 |
| q1 | 0.628 | 0.939 | 61 |
| q2 | 0.702 | 0.945 | 62 |
| q3 | 0.657 | 0.985 | 56 |
| q4 | 0.823 | 1.004 | 60 |

**Interpretation (honest reframe).** All three predictors decline on gappy columns. Because even position/MSA-blind BLOSUM62 declines (0.244→0.119), the degradation is **intrinsic to hard-to-align positions, not an AM-specific generalisation failure**. AM is highest at every bin and declines least (q4→q0: AM 0.120 vs PSSM 0.172) → **AM is the most robust predictor**, with its largest margin over the MSA baseline exactly where alignment is hardest. The deep-column interaction degrades AM (0.475→0.305) and PSSM (0.435→0.274) by similar margins (shared, not AM-specific). DMS dynamic range shrinks ~27% (insert) → part of the |Spearman| decline reflects reduced measurable signal, not predictor error. Adding the baselines was decisive: without them the v1 figure would have over-claimed an AM-specific failure the data does not support.

Files: `figure_axis3_SPC_v2.{pdf,svg,png}`, `figure_axis3_SPC_v2_data.tsv`, `axis3_baselines_binstats.tsv`, `axis3_dms_signal_perbin.tsv`, `pssm_counts.tsv`, `cartoon_columns.json`.

