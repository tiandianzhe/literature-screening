"""
Deduplicate & Filter Non-Research Papers
Usage: python dedup_filter.py --input results.csv --output dedup.csv
"""
import argparse, csv, re
from difflib import SequenceMatcher

RESEARCH_TYPES = {
    "Journal Article", "Review", "Clinical Trial", "Meta-Analysis",
    "Randomized Controlled Trial", "Comparative Study", "Evaluation Study",
    "Multicenter Study", "Observational Study", "Pragmatic Clinical Trial",
}
NON_RESEARCH = {
    "Editorial", "Letter", "Comment", "News", "Retraction of Publication",
    "Published Erratum", "Historical Article", "Biography", "Portrait",
    "Interview", "Congress", "Festschrift", "Lecture", "Video-Audio Media",
    "Personal Narrative", "Autobiography", "Bibliography", "Directory",
    "Patient Education Handout", "Newspaper Article", "Webcast",
}

def title_similar(t1, t2):
    return SequenceMatcher(None, t1.lower(), t2.lower()).ratio()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    articles = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            articles.append(row)

    orig = len(articles)
    print(f"Loaded: {orig} articles")

    # Step 1: Remove exact PMID duplicates
    seen_pmids = set()
    dedup = []
    for a in articles:
        if a["PMID"] not in seen_pmids:
            dedup.append(a)
            seen_pmids.add(a["PMID"])
    print(f"  After PMID dedup: {len(dedup)} (removed {orig - len(dedup)})")

    # Step 2: Remove near-duplicate titles
    articles2 = []
    skipped_titles = 0
    for i, a in enumerate(dedup):
        dup = False
        for j in range(max(0, i-3), i):
            if title_similar(a.get("title",""), dedup[j].get("title","")) > 0.9:
                dup = True
                break
        if dup:
            skipped_titles += 1
        else:
            articles2.append(a)
    print(f"  After title dedup: {len(articles2)} (removed {skipped_titles})")

    # Step 3: Filter by publication type
    kept = []
    no_type = 0
    filtered_types = {}
    for a in articles2:
        pts = set(re.split(r";\s*", a.get("pub_type", "")))
        is_research = any(pt in RESEARCH_TYPES for pt in pts)
        is_non_research = any(pt in NON_RESEARCH for pt in pts)
        if is_research:
            kept.append(a)
        elif not is_non_research:
            no_type += 1
            kept.append(a)  # 未分类的保留
        else:
            for pt in pts & NON_RESEARCH:
                filtered_types[pt] = filtered_types.get(pt, 0) + 1

    print(f"  After type filter: {len(kept)} (kept {no_type} unclassified)")
    print(f"  Filtered out by type:")
    for pt, count in sorted(filtered_types.items(), key=lambda x: -x[1])[:10]:
        print(f"    {pt}: {count}")

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=kept[0].keys())
        writer.writeheader()
        writer.writerows(kept)
    print(f"\nSaved {len(kept)} to {args.output}")

if __name__ == "__main__":
    main()
