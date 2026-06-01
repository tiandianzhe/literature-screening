"""
Multi-Dimensional LLM Scoring
Usage: python multi_dim_score.py --input dedup.csv --output scored.csv \
    --dimensions "GENE,TARGET,DRUG,VALID,CLIN" --api-key $KEY [--base-url URL]
"""
import argparse, csv, json, os, time, sys
from openai import OpenAI

# Define common dimension sets. User overrides via --dimensions.
DIMENSION_TEMPLATES = {
    "drug_target": {
        "GENE": "Paper studies a specific gene/protein by name (not general pathways)",
        "TARGET": "Gene/protein is discussed as a therapeutic target for disease",
        "DRUG": "Specific drug, small molecule, or biologic is mentioned by name",
        "VALID": "Includes experimental validation (in vitro, in vivo, or clinical data)",
        "CLIN": "Contains clinical data, patient samples, or trial results",
        "MECH": "Describes molecular mechanism or signaling pathway",
        "BIOM": "Discusses biomarkers, prognosis, or diagnostic markers",
        "REVIEW": "Is a review article (score 1 for review, 0 otherwise)",
    },
    "biomarker": {
        "BIOMARKER": "Identifies or validates a specific biomarker",
        "COHORT": "Has a defined patient cohort with sample size",
        "SENSITIVITY": "Reports sensitivity/specificity or AUC values",
        "PROGNOSIS": "Links biomarker to clinical outcomes (OS, PFS, RFS)",
        "VALIDATION": "Includes independent validation cohort",
        "MULTICENTER": "Multi-center or multi-cohort study",
        "METHOD": "Describes assay methodology in detail",
        "UTILITY": "Discusses clinical utility or implementation",
    },
}


def build_scoring_prompt(title, abstract, dimensions):
    dim_text = "\n".join(f"- {k}: {v}" for k, v in dimensions.items())
    dim_keys = ", ".join(dimensions.keys())
    return f"""Score this biomedical paper on {len(dimensions)} dimensions.
Each dimension: 0 = not present, 1 = present.

Title: {title}
Abstract: {abstract[:1200]}

Dimensions:
{dim_text}

Respond with ONLY a JSON object, no other text:
{{"DIM1": 0, "DIM2": 1, ...}}"""


def main():
    parser = argparse.ArgumentParser(description="Multi-Dimension LLM Scoring")
    parser.add_argument("--input", required=True, help="Input CSV from dedup_filter")
    parser.add_argument("--output", required=True, help="Output CSV with scores")
    parser.add_argument("--dimensions", required=True,
        help="Comma-separated dimension names, OR a preset name: drug_target, biomarker")
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--base-url", default="https://api.deepseek.com")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--limit", type=int, default=0, help="Max papers to score (0=all)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    args = parser.parse_args()

    # Resolve dimensions
    if args.dimensions in DIMENSION_TEMPLATES:
        dims = DIMENSION_TEMPLATES[args.dimensions]
        print(f"Using preset: {args.dimensions}")
    else:
        # Custom dimensions — generate generic descriptions
        keys = [k.strip() for k in args.dimensions.split(",")]
        dims = {k: f"Paper contains information about {k.lower()}" for k in keys}
        print(f"Using custom dimensions: {list(dims.keys())}")

    # Load papers
    papers = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            papers.append(row)
    print(f"Loaded {len(papers)} papers")

    if args.limit > 0:
        papers = papers[:args.limit]
        print(f"  Limited to {args.limit}")

    # Resume support
    checkpoint_file = args.output.replace(".csv", "_checkpoint.jsonl")
    scored_pmids = set()
    if args.resume and os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            for line in f:
                r = json.loads(line)
                scored_pmids.add(r["PMID"])
        print(f"  Resuming: {len(scored_pmids)} already scored")

    # API client
    client = OpenAI(api_key=args.api_key, base_url=args.base_url)

    # Score
    fieldnames = list(papers[0].keys()) + list(dims.keys()) + ["TOTAL"]
    out_rows = []
    checkpoint_fh = open(checkpoint_file, "a", encoding="utf-8")

    for i, paper in enumerate(papers):
        if paper["PMID"] in scored_pmids:
            continue

        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        if not abstract.strip():
            abstract = title  # fallback

        prompt = build_scoring_prompt(title, abstract, dims)

        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=args.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200, temperature=0.1,
                )
                content = resp.choices[0].message.content.strip()
                # Extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                scores = json.loads(content)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"  Failed {paper['PMID']}: {e}")
                    scores = {k: 0 for k in dims}
                time.sleep(2 ** attempt)

        total = sum(scores.get(k, 0) for k in dims)
        row = dict(paper)
        row.update(scores)
        row["TOTAL"] = total
        out_rows.append(row)

        # Checkpoint
        ckpt = dict(paper)
        ckpt.update(scores)
        ckpt["TOTAL"] = total
        checkpoint_fh.write(json.dumps(ckpt) + "\n")
        checkpoint_fh.flush()

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(papers)} | avg score: {sum(r['TOTAL'] for r in out_rows)/len(out_rows):.1f}")

        time.sleep(0.2)  # rate limit

    checkpoint_fh.close()

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"\nSaved {len(out_rows)} scored papers to {args.output}")

    # Distribution
    totals = [r["TOTAL"] for r in out_rows]
    from collections import Counter
    dist = Counter(totals)
    print("\nScore distribution:")
    for s in range(max(totals), -1, -1):
        count = dist.get(s, 0)
        bar = "#" * (count // max(1, max(dist.values()) // 30))
        print(f"  {s}: {count:5d} |{bar}")


if __name__ == "__main__":
    main()
