import argparse
import subprocess
import sys
from pathlib import Path

from .pipeline import build_project, render_map


def main():
    p = argparse.ArgumentParser(prog="litmap")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="search + cluster, writes interpretation.csv")
    b.add_argument("-q", "--query", action="append", required=True, help="repeatable")
    b.add_argument("--source", choices=["openalex", "semantic_scholar"], default="openalex")
    b.add_argument("--search-in", choices=["title_abstract", "title", "abstract", "fulltext", "all"],
                   default="title_abstract", help="fields to match the query against (OpenAlex; "
                   "Semantic Scholar supports title_abstract only)")
    b.add_argument("--out", default="project")
    b.add_argument("--max-results", type=int, default=5000, help="per query; 0 = all results")
    b.add_argument("--from-year", type=int)
    b.add_argument("--to-year", type=int)
    b.add_argument("--email", help="OpenAlex polite pool")
    b.add_argument("--min-cluster-size", type=int, default=30)

    r = sub.add_parser("render", help="interpretation.csv + dataset -> map.html")
    r.add_argument("project")
    r.add_argument("--interpretation")
    r.add_argument("--title")
    r.add_argument("--light", action="store_true")

    sub.add_parser("app", help="launch the Streamlit UI")

    a = p.parse_args()
    if a.cmd == "build":
        build_project(a.query, a.source, a.out, a.max_results, a.from_year, a.to_year,
                      a.email, search_in=a.search_in, min_cluster_size=a.min_cluster_size)
    elif a.cmd == "render":
        print(render_map(a.project, a.interpretation, title=a.title, darkmode=not a.light))
    else:
        app = Path(__file__).with_name("app.py")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)])


if __name__ == "__main__":
    main()
