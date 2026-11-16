from . import openalex, semantic_scholar

SOURCES = {
    "openalex": openalex.search,
    "semantic_scholar": semantic_scholar.search,
}
