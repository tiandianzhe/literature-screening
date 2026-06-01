"""
PubMed Literature Search
Usage: python pubmed_search.py --query "QUERY_STRING" --output results.csv [--email user@example.com] [--mindate 2015 --maxdate 2026]
"""
import argparse, csv, time
from Bio import Entrez

def search_pubmed(query, email, mindate="2015", maxdate="2026", retmax=9999):
    """Execute PubMed search with history, return total count and fetch metadata."""
    Entrez.email = email
    print(f"Searching PubMed...")
    print(f"  Query: {query[:120]}...")
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax,
        mindate=f"{mindate}/01/01", maxdate=f"{maxdate}/12/31",
        datetype="pdat", usehistory="y")
    record = Entrez.read(handle); handle.close()
    total = int(record["Count"])
    webenv = record["WebEnv"]
    query_key = record["QueryKey"]
    print(f"  Total results: {total}")
    return total, webenv, query_key

def fetch_details(webenv, query_key, total, email, batch_size=200):
    """Fetch title, abstract, pub type, year for all PMIDs."""
    Entrez.email = email
    results = []
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        print(f"  Fetching {start+1}-{end}/{total}...", end=" ")
        handle = Entrez.efetch(db="pubmed", rettype="xml", retmode="xml",
            retstart=start, retmax=batch_size,
            webenv=webenv, query_key=query_key)
        records = Entrez.read(handle); handle.close()
        count = 0
        for article in records.get("PubmedArticle", []):
            try:
                medline = article["MedlineCitation"]
                pmid = str(medline["PMID"])
                title = str(medline["Article"].get("ArticleTitle", ""))
                abstract = " ".join(str(a) for a in medline["Article"].get("Abstract", {}).get("AbstractText", []))
                pub_types = [str(pt) for pt in medline["Article"].get("PublicationTypeList", [])]
                year = str(medline.get("DateCompleted", {}).get("Year", "")) or \
                       str(article.get("PubmedData", {}).get("History", [{}])[0].get("Year", ""))
                results.append({"PMID": pmid, "title": title, "abstract": abstract,
                    "pub_type": "; ".join(pub_types), "year": year})
                count += 1
            except Exception:
                continue
        print(f"{count} articles")
        time.sleep(0.5)
    return results

def main():
    parser = argparse.ArgumentParser(description="PubMed Literature Search")
    parser.add_argument("--query", required=True, help="PubMed query string")
    parser.add_argument("--output", required=True, help="Output CSV file path")
    parser.add_argument("--email", default="research@example.com", help="Email for Entrez API")
    parser.add_argument("--mindate", default="2015", help="Minimum publication year")
    parser.add_argument("--maxdate", default="2026", help="Maximum publication year")
    args = parser.parse_args()

    total, webenv, query_key = search_pubmed(args.query, args.email, args.mindate, args.maxdate)
    results = fetch_details(webenv, query_key, total, args.email)

    with open(args.output, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["PMID", "title", "abstract", "pub_type", "year"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSaved {len(results)} articles to {args.output}")

if __name__ == "__main__":
    main()
