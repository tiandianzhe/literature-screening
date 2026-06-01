---
name: literature-screening
description: |
  Systematic literature screening pipeline for biomedical research: 
  keyword design → PubMed search → dedup & filter non-research → 
  multi-dimensional LLM scoring → quality threshold selection.
  This skill should be used when the user needs to conduct a systematic 
  literature search and screening, wants to filter papers by relevance 
  and quality, or mentions terms like "文献筛选", "文献检索", "PubMed 
  search", "literature scoring", "论文打分", "系统检索".
agent_created: true
---

# Literature Screening Pipeline

A reusable 5-step pipeline for systematic biomedical literature screening. Each step is
implemented as a reusable Python script in `scripts/`.

## Trigger Conditions

Invoke this skill when the user:
- Wants to search and screen literature for a new research topic
- Mentions "文献筛选", "文献检索", "systematic screening", "PubMed scoring"
- Needs to establish a curated corpus from PubMed for downstream analysis (LLM fine-tuning, meta-analysis, systematic review)

## Pipeline Overview

```
Step 1: Design Keywords → Step 2: PubMed Search → Step 3: Dedup & Filter
→ Step 4: Multi-Dim Scoring → Step 5: Quality Threshold Selection
```

## Workflow

### Step 1: Keyword Design

Before any search, work with the user to design PubMed query keywords using this strategy:

1. **Disease terms**: Combine MeSH terms + free-text variants (e.g., "Carcinoma, Hepatocellular"[Mesh] OR hepatocellular carcinoma[tiab] OR HCC[tiab])
2. **Topic terms**: Use field-specific MeSH terms + free-text variants (e.g., "drug target*"[tiab] OR "therapeutic target*"[tiab])
3. **Join with AND**: Disease AND Topic
4. **Date filter**: Typically 2015–present
5. **Validate**: Run a small test query to check result count. If >10,000, add more restrictive terms. If <500, broaden.

Reference: `references/keyword_design.md`

### Step 2: PubMed Search

Use `scripts/pubmed_search.py`:

```bash
python scripts/pubmed_search.py --query "YOUR_QUERY" --output results.csv
```

The script:
- Uses Entrez.esearch with history (WebEnv) for large result sets
- Fetches title, abstract, publication type, year for all results
- Saves as CSV with columns: PMID, title, abstract, pub_type, year

**Rate limit**: 3 requests/second with Entrez API key (10/sec); 1/sec without.

### Step 3: Deduplicate & Filter Non-Research Papers

Use `scripts/dedup_filter.py`:

```bash
python scripts/dedup_filter.py --input results.csv --output dedup.csv
```

The script:
- Removes exact duplicate PMIDs and near-duplicate titles (edit distance < 5)
- Filters out non-research publication types: Editorial, Letter, Comment, News, Retraction, etc.
- Keeps: Journal Article, Review, Clinical Trial, Meta-Analysis, Randomized Controlled Trial
- Reports filtering statistics

### Step 4: Multi-Dimensional Scoring

This is the core step. Use `scripts/multi_dim_score.py`:

```bash
python scripts/multi_dim_score.py --input dedup.csv --output scored.csv --dimensions "GENE,TARGET,DRUG,VALID,CLIN,MECH,BIOM,REVIEW" --api-key $DEEPSEEK_KEY
```

**How scoring works:**

Each paper is scored 0/1 on multiple dimensions by an LLM (DeepSeek V4 Pro). The LLM reads the title + abstract and judges whether the paper contains information relevant to each dimension.

**Dimension selection is THE critical design decision.** Choose dimensions based on the research question:

| Research Type | Example Dimensions |
|--------------|-------------------|
| Drug target discovery | GENE (gene studied), TARGET (therapeutic target), DRUG (drug/small molecule), VALID (experimental validation), CLIN (clinical relevance), MECH (mechanism), BIOM (biomarker), REVIEW (review article) |
| Clinical biomarker | BIOMARKER, COHORT, SENSITIVITY, SPECIFICITY, CUTOFF, PROGNOSIS, VALIDATION, MULTICENTER |
| Meta-analysis | EFFECT_SIZE, CONFIDENCE_INTERVAL, SAMPLE_SIZE, HETEROGENEITY, PUBLICATION_BIAS, SUBGROUP, SENSITIVITY_ANALYSIS, FOLLOW_UP |
| Genomic association | GWAS, SNP, ODDS_RATIO, REPLICATION, POPULATION, LINKAGE, FUNCTIONAL, ANNOTATION |

**Scoring prompt template:** The script constructs a prompt for each paper. Customize the dimension definitions in the script's `DIMENSIONS` dict for each research direction.

Reference: `references/scoring_dimensions.md`

**API config:**
- Model: `deepseek-chat` (or `deepseek-reasoner` for complex dimensions)
- Max tokens: 500 per paper
- Cost: ~0.3 RMB per 1000 papers
- Checkpoint: saves progress every 50 papers for resume capability

### Step 5: Quality Threshold Selection

Use `scripts/select_papers.py`:

```bash
python scripts/select_papers.py --input scored.csv --threshold 3 --output selected.csv
```

The script:
- Computes TOTAL = sum of all dimension scores
- Displays score distribution histogram
- Lets user choose threshold based on:
  - **Desired corpus size** (e.g., "I want ~3,000 papers")
  - **Quality floor** (e.g., "at least 3 out of 8 dimensions")
  - **Score distribution** (natural breaks in the curve)
- Outputs filtered CSV with papers meeting threshold

**Typical thresholds:**
- TOTAL >= 3: ~35-40% of deduplicated papers (good for LLM training)
- TOTAL >= 5: ~10-15% (high-quality papers for gold standard)
- TOTAL >= 7: ~2-5% (top-tier only)

### Post-Pipeline

After selection, the curated corpus can be used for:
- **LLM fine-tuning**: chunk papers → generate QA pairs → SFT
- **Meta-analysis**: extract effect sizes and study characteristics
- **Systematic review**: PRISMA flow diagram, risk of bias
- **Knowledge base**: ingest into vector DB for RAG

## Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/pubmed_search.py` | Execute PubMed search with history | Query string | `results.csv` (PMID, title, abstract, pub_type, year) |
| `scripts/dedup_filter.py` | Remove duplicates and non-research | `results.csv` | `dedup.csv` |
| `scripts/multi_dim_score.py` | Multi-dimension LLM scoring | `dedup.csv` | `scored.csv` (original columns + dimension columns + TOTAL) |
| `scripts/select_papers.py` | Select papers by score threshold | `scored.csv` | `selected.csv` |

## References

- `references/scoring_dimensions.md` — Detailed guide for choosing scoring dimensions based on research type
- `references/keyword_design.md` — PubMed query construction best practices
