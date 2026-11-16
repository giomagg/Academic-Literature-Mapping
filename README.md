# litmap

Search OpenAlex or Semantic Scholar, cluster the abstracts, label the clusters, and draw an interactive literature map.

## Install
    pip install -e .

## Workflow
1. run `litmap build -q '"far-right" OR "radical right"' -q populism --out project`
   Writes `project/interpretation.csv` (cluster, n_docs, keywords, top_titles, empty `label`).
2. Fill in the `label` column in the output csv file. Empty labels fall back to the keywords; clusters sharing a label are merged on the map.
3. `litmap render project` writes `project/map.html`.

Or run `litmap app` for the Streamlit UI (search, edit labels in a table, re-render).

From Python:

    from litmap import build_project, render_map
    build_project(['"far-right" OR "radical right"'], out_dir="project")
    render_map("project", title="Far right & populism")

CLI Commands and Options

The application provides three commands: build, render, and app.

1. build — Search and Cluster Publications

Searches academic publications, performs clustering, and generates interpretation.csv.

Usage:

bash
python main.py build -q "research topic" [options]

Flag	Default	Description
-q, --query	Required	Search query. Can be repeated to search multiple topics.
--source	openalex	Academic database: openalex or semantic_scholar.
--search-in	title_abstract	Fields to search: title_abstract, title, abstract, fulltext, or all. Semantic Scholar supports title_abstract only.
--out	project	Output project directory.
--max-results	5000	Maximum publications per query. Use 0 for all available results.
--from-year	None	Earliest publication year.
--to-year	None	Latest publication year.
--email	None	Email address for OpenAlex polite pool access.
--min-cluster-size	30	Minimum number of publications required to form a cluster.

Example:

bash
python main.py build \
    -q "artificial intelligence in healthcare" \
    -q "machine learning in medicine" \
    --source openalex \
    --from-year 2020 \
    --to-year 2025 \
    --max-results 5000 \
    --min-cluster-size 30 \
    --out healthcare_ai

2. render — Generate Interactive Research Map

Generates an interactive map.html visualization using the project dataset and interpretation results.

Usage:

bash
python main.py render PROJECT [options]

Argument / Flag	Default	Description
project	Required	Path to the project directory.
--interpretation	None	Custom path to interpretation.csv.
--title	None	Custom title for the research map.
--light	False	Enables the light visualization theme.

Example:

bash
python main.py render healthcare_ai \
    --title "AI Research Landscape" \
    --light

3. app — Launch Graphical Interface

Launches the Streamlit application.

Usage:
```
python limap app
```

No additional arguments are required.

Typical Workflow
```
# 1. Search publications and perform clustering
litmap build -q "artificial intelligence" --out project

# 2. Generate the interactive research map
litmap render project --title "AI Research Landscape"

# 3. Launch the graphical interface (optional)
litmap app
```