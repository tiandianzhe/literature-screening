# Scoring Dimension Design Guide

## Principle

Scoring dimensions must be:
1. **Binary** (0 or 1) — no ambiguity in LLM judgment
2. **Independent** — each dimension measures a distinct aspect
3. **Relevant** — aligned with the research question
4. **Abstract-detectable** — LLM can judge from title + abstract alone

## Dimension Templates by Research Type

### Drug Target Discovery
| Dimension | Definition | Why Include |
|-----------|-----------|-------------|
| GENE | Paper studies a named gene/protein | Core — identifies papers with gene-level information |
| TARGET | Gene discussed as therapeutic target | Core — separates mechanistic from therapeutic focus |
| DRUG | Specific drug/molecule mentioned | Core — drug-target interaction evidence |
| VALID | Experimental validation (in vitro/in vivo) | Filters out purely computational papers |
| CLIN | Clinical data or patient samples | Up-weights translational relevance |
| MECH | Molecular mechanism described | Captures mechanistic depth |
| BIOM | Biomarker or prognostic information | Clinical utility signal |
| REVIEW | Review/overview article | Separates primary from secondary literature |

**Our HCC case**: Used GENE, TARGET, DRUG, VALID, CLIN, MECH, BIOM, REVIEW (8 dims).
**Why not include**: DISEASE_SPECIFIC (all papers are HCC), PUBLICATION_VENUE (not in abstract).

### Clinical Biomarker Discovery
| Dimension | Definition |
|-----------|-----------|
| BIOMARKER | Specific biomarker named and studied |
| COHORT | Defined patient population with N |
| SENSITIVITY | Performance metrics reported (AUC, sens/spec) |
| PROGNOSIS | Linked to clinical outcomes |
| VALIDATION | Independent validation |
| MULTICENTER | Multi-site or multi-cohort |
| METHOD | Assay/protocol detail |
| UTILITY | Clinical applicability discussed |

### Meta-Analysis Screening
| Dimension | Definition |
|-----------|-----------|
| EFFECT_SIZE | Reports effect size (OR, RR, HR, SMD) |
| CONFIDENCE_INTERVAL | Reports CI |
| SAMPLE_SIZE | N > 100 per group |
| HETEROGENEITY | Reports I² or Q statistic |
| PUBLICATION_BIAS | Assesses publication bias |
| SUBGROUP | Subgroup analysis present |
| SENSITIVITY_ANALYSIS | Sensitivity analysis present |
| FOLLOW_UP | Longitudinal data |

### Genomic Association
| Dimension | Definition |
|-----------|-----------|
| GWAS | Genome-wide approach |
| SNP | Specific variants identified |
| ODDS_RATIO | Effect size reported |
| REPLICATION | Replication cohort |
| POPULATION | Population described |
| LINKAGE | Linkage or fine-mapping |
| FUNCTIONAL | Functional annotation |
| ANNOTATION | Variant annotation |

## Custom Dimension Design Checklist

When designing custom dimensions:
1. **Start with 5-8 dimensions** (too many = noise, too few = no differentiation)
2. **Define each dimension precisely** in the prompt — avoid vague terms
3. **Test on 20 papers** manually to calibrate before running full batch
4. **Check score distribution** — should be roughly normal, not all zeros or all high
5. **Adjust definitions** if a dimension gives the same score for >90% of papers

## Dimension Anti-Patterns

- **Too specific**: "Mentions RT-qPCR validation" (too rare, won't differentiate)
- **Too broad**: "Is about cancer" (all papers will score 1)
- **Ambiguous**: "Is interesting" (LLM can't judge reliably)
- **Redundant**: "TARGET" and "DRUGGABLE" (highly correlated, pick one)
- **Not in abstract**: "Has supplement with validation data" (LLM can't see supplement)
