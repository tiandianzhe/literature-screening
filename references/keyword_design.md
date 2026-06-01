# PubMed Keyword Design Guide

## Query Structure

```
(DISEASE_TERMS) AND (TOPIC_TERMS) AND [optional: FILTERS]
```

## Disease Term Construction

Always combine MeSH + free-text for recall:

```text
("Disease Name"[Mesh] OR disease name[tiab] OR variant 1[tiab] OR variant 2[tiab])
```

**Examples:**

| Disease | Query Fragment |
|---------|---------------|
| HCC | `("Carcinoma, Hepatocellular"[Mesh] OR hepatocellular carcinoma[tiab] OR liver cancer[tiab] OR HCC[tiab])` |
| Diabetes | `("Diabetes Mellitus"[Mesh] OR diabetes[tiab] OR T2DM[tiab] OR type 2 diabetes[tiab])` |
| Alzheimer's | `("Alzheimer Disease"[Mesh] OR Alzheimer*[tiab] OR AD[tiab])` |

**Tips:**
- Check MeSH browser (https://meshb.nlm.nih.gov/) for official terms
- Include abbreviation variants (HCC, T2DM, AD)
- Use `[tiab]` for title+abstract, not `[tw]` (which includes author keywords, often noisy)

## Topic Term Construction

Layer specificity with OR groups:

```text
(aspect 1[tiab] OR aspect 2[tiab] OR aspect 3[tiab])
```

**Examples by research type:**

| Research Type | Topic Fragment |
|--------------|---------------|
| Drug target | `(drug target*[tiab] OR therapeutic target*[tiab] OR druggable[tiab] OR target discovery[tiab])` |
| Biomarker | `(biomarker*[tiab] OR prognostic marker*[tiab] OR diagnostic marker*[tiab] OR predictive marker*[tiab])` |
| Immunotherapy | `(immunotherapy[tiab] OR immune checkpoint[tiab] OR CAR-T[tiab] OR PD-1[tiab] OR PD-L1[tiab])` |
| Genomics | `(genomics[tiab] OR GWAS[tiab] OR transcriptom*[tiab] OR whole exome[tiab] OR sequencing[tiab])` |

## Optional Filters

| Filter | Syntax | When to Use |
|--------|--------|-------------|
| Date range | `AND ("2015"[Date - Publication] : "2026"[Date - Publication])` | Always |
| Language | `AND english[Language]` | Usually |
| Article type | `AND (Journal Article[ptyp] OR Review[ptyp])` | If you want to filter BEFORE download (not recommended — filter after) |
| Human only | `AND humans[MeSH Terms]` | For clinical research |

## Query Validation

Before full run:
1. Test query in PubMed web interface → check first 20 results for relevance
2. If >10,000 results → add more restrictive terms
3. If <200 results → broaden terms (remove restrictive ones, add wildcards)
4. Spot-check: are the top 10 papers exactly what you'd expect?

## Common Pitfalls

- **Too narrow**: Adding too many AND clauses → 50 results, missing important papers
  - Fix: Remove lowest-priority AND clause, test again
- **Too broad**: Generic terms like "cancer[tiab]" → 500,000+ results
  - Fix: Use MeSH terms, add specificity
- **Missing MeSH**: Not using MeSH → misses papers with different terminology
  - Fix: Always include MeSH term as OR alternative
- **Truncation misuse**: `therap*` matches "therapist", "therapeutic", "therapy"
  - Fix: Be specific: `therap*[tiab]` is usually fine for title/abstract
