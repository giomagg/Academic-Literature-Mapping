# `litmap` – mapping academic landscapes

Create interactive semantic literature maps from OpenAlex or Semantic Scholar search. This can be used by scholars and practitioners for quantitative literature reviews or exploratory search of their field's composition. See example maps on [politicisation](https://giomagg.github.io/projects/html_maps/Politicisation.html), [mainstreaming](https://giomagg.github.io/projects/html_maps/Political-Mainstreaming.html), and [disinformation](https://giomagg.github.io/projects/html_maps/Disinformation.html).

You need an API key to use: 
- For OpenAlex create an account, and then receive your free key from https://openalex.org/settings/api-key 
- For Semantic Scholars request a temporary API key at https://www.semanticscholar.org/product/api#api-key-form

## Install
```
git clone https://github.com/giomagg/Academic-Literature-Mapping.git    
cd Academic-Literature-Mapping
python -m venv venv
pip install -e .
```

## Use
### CLI 
**Step 1.** Run build with search terms and parameters. This writes `project/interpretation.csv` with columns (cluster, n_docs, keywords, top_titles, empty `label`).

```
litmap build -q '"far-right" OR "radical right"' -q populism --out project --source openalex
```

**Step 2.** Open the `interpretation.csv` and fill in the `label` column. This step is necessary to create labels concise for the final interactive map. Empty labels fall back onto the keywords; clusters sharing the same label are merged into one on the map.

**Step 3.** Run render, visualise map (`project/map.html`) and iteratively adjust labels. 

```
litmap render project
```

See full CLI flag options below 

### Python
```
from litmap import build_project, render_map
build_project(['"far-right" OR "radical right"'], out_dir="project")
render_map("project", title="Far right & populism")
```

### Streamlit app 
You can also run `litmap` through a **Streamlit UI** in your browser (search, edit labels in a table, re-render). Simply run:

```
litmap app
```


### CLI Options
#### `build`
```
litmap build -q "research topic" [options]

Flag	            Default	        Description
-q, --query	        Required	    Search query. Can be repeated to search multiple topics.
--source	        openalex	    Academic database: openalex or semantic_scholar.
--search-in	        title_abstract	Fields to search: title_abstract, title, abstract, fulltext, 
                                    or all. Semantic Scholar supports title_abstract only.
--out	            project	        Output project directory.
--max-results       5000	        Max publications per query. NOTE: Use 0 to retrieve ALL available results.
--from-year	        None	        Earliest publication year.
--to-year	        None	        Latest publication year.
--min-cluster-size	30	    Minimum number of publications required to form a cluster in HDBSCAN.
```
Example:
```
litmap build \
    -q "Far-right" \
    -q "populism" \
    --source openalex \
    --from-year 2020 \
    --to-year 2025 \
    --max-results 10000 \
    --min-cluster-size 30 \ 
    --out far_righ_research
```

#### `render` 
```
litmap render PROJECT [options]

Flag	            Default	    Description
project	            Required	Path to the project directory.
--interpretation	None	    Custom path to interpretation.csv.
--title	            None	    Custom title for the research map.
--light	            False	    Enables the light visualization theme (default is dark theme).
```
Example:

```
litmap render far_righ_research \
    --title "Far-right Research Landscape" \
    --light
```

#### `app`
This launches the Streamlit application. No additional arguments are required.
```
litmap app
``` 

Cite: Giovanni Maggi (2026). litmap – map the academic landscape. https://github.com/giomagg/Academic-Literature-Mapping