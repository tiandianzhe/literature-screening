"""
Select Papers by Quality Threshold
Usage: python select_papers.py --input scored.csv --threshold 3 --output selected.csv
"""
import argparse, csv
from collections import Counter

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--threshold", type=int, default=3, help="Minimum TOTAL score")
    args = parser.parse_args()

    papers = []
    with open(args.input, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            papers.append(row)

    totals = [int(r["TOTAL"]) for r in papers]
    dist = Counter(totals)
    max_score = max(totals) if totals else 0

    # Show distribution
    print(f"Total papers: {len(papers)}")
    print(f"Score range: 0-{max_score}")
    print(f"Mean score: {sum(totals)/len(totals):.2f}")
    print()
    print("Score distribution:")
    print(f"  {'Score':<8} {'Count':<8} {'Cumulative':<12} {'% Kept':<10}")
    print(f"  {'-'*8} {'-'*8} {'-'*12} {'-'*10}")

    cumulative = 0
    for s in range(max_score, -1, -1):
        cumulative += dist.get(s, 0)
        pct = cumulative / len(papers) * 100
        marker = " <--" if s == args.threshold else ""
        print(f"  {s:<8} {dist.get(s, 0):<8} {cumulative:<12} {pct:<10.1f}{marker}")

    # Select
    selected = [r for r in papers if int(r["TOTAL"]) >= args.threshold]
    print(f"\nThreshold: TOTAL >= {args.threshold}")
    print(f"Selected: {len(selected)} / {len(papers)} ({len(selected)/len(papers)*100:.1f}%)")
    print(f"Discarded: {len(papers) - len(selected)}")

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=papers[0].keys())
        writer.writeheader()
        writer.writerows(selected)
    print(f"\nSaved {len(selected)} to {args.output}")

if __name__ == "__main__":
    main()
