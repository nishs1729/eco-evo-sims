#!/usr/bin/env python3
"""A01 novelty search for Project A, using the OpenAlex API (no sign-in needed).

Runs the Boolean searches from ROADMAP §1.1 (adapted to OpenAlex syntax) and
chases citations backward (references) and forward (citing works) from the
anchor papers. Writes every hit, with the queries that found it, to
projectA/results/novelty/hits.json, plus a log of queries and counts.

Usage:  python3 projectA/src/novelty_search.py
"""
import json
import pathlib
import time
import urllib.parse
import urllib.request

API = "https://api.openalex.org/works"
OUT = pathlib.Path(__file__).resolve().parents[1] / "results" / "novelty"
# OpenAlex allows 1 request/s for Boolean searches with >5 operators (no API key).
PAUSE = 1.2
FIELDS = ("id,doi,title,publication_year,cited_by_count,type,primary_location,"
          "authorships,abstract_inverted_index,referenced_works")

# Boolean searches over title + abstract. Uppercase AND/OR/NOT, quoted phrases, no * wildcards.
SEARCHES = {
    "S1_model_calibration": (
        '("tropical forest" OR "rain forest" OR rainforest OR "wet evergreen") AND '
        '("individual-based" OR "gap model" OR "forest simulator" OR "forest model" OR FORMIND OR TROLL '
        'OR "perfect plasticity") AND ("Bayesian calibration" OR "approximate Bayesian" OR '
        '"simulation-based inference" OR "neural posterior" OR "inverse modelling" OR "inverse modeling" '
        'OR parameterization OR parameterisation OR calibration)'),
    "S2_WG_demography_climate": (
        '"Western Ghats" AND (mortality OR growth OR recruitment OR demography OR dynamics) AND '
        '(drought OR "water deficit" OR climate OR rainfall OR "dry season")'),
    "S3_Uppangala": 'Uppangala',
    "S4_monsoon_tree_drought": (
        '("tree mortality" OR "tree growth" OR "stem mortality" OR "diameter growth") AND '
        '("dry season" OR "water deficit" OR drought) AND (monsoon OR India OR "South Asia")'),
    "S5_WG_plots": (
        '"Western Ghats" AND ("permanent plot" OR "permanent sample plot" OR "long-term plot" OR '
        '"forest dynamics" OR census OR "forest model" OR "simulation model")'),
    "S6_Anamalai_Valparai": '(Anamalai OR Valparai) AND (tree OR forest) AND (plot OR census OR dynamics)',
    "S7_SBI_vegetation": (
        '("simulation-based inference" OR "neural posterior estimation" OR "neural likelihood" OR '
        '"amortized inference" OR "amortised inference") AND (forest OR vegetation OR "individual-based" '
        'OR "agent-based" OR ecology OR ecological)'),
    "S8_climate_IBM_projection": (
        '("tropical forest" OR "tropical trees") AND ("individual-based" OR "forest model" OR '
        '"demographic model" OR "integral projection") AND (CMIP6 OR CMIP5 OR "climate projections" '
        'OR "climate change scenarios") AND (mortality OR demography OR demographic)'),
}

# Anchor papers for citation chasing (ROADMAP §1.1).
ANCHORS = {
    "Ruger2020_Science": "10.1126/science.aaz4797",
    "Hartig2014_Biogeosciences": "10.5194/bg-11-1261-2014",
    "Pelissier2011_Ecology": "10.1890/10-1991.1",
    "Bennett2015_NatPlants": "10.1038/nplants.2015.139",
}


def get(url, params):
    q = urllib.parse.urlencode(params, safe=":,|*")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(f"{url}?{q}", timeout=60) as r:
                return json.load(r)
        except Exception:  # rate limits (429/401) and transient errors: back off and retry
            if attempt == 4:
                raise
            time.sleep(2 + 2 ** attempt)
    return None


def fetch_all(filter_str, cap=3000):
    # Page-number paging: cursor paging past page 1 needs an API key.
    out, page = [], 1
    while len(out) < cap:
        d = get(API, {"filter": filter_str, "per-page": 200, "page": page, "select": FIELDS})
        out += d["results"]
        time.sleep(PAUSE)
        if len(d["results"]) < 200 or len(out) >= d["meta"]["count"]:
            break
        page += 1
    return out, d["meta"]["count"]


def fetch_ids(ids):
    out = []
    for i in range(0, len(ids), 50):
        chunk = "|".join(x.rsplit("/", 1)[-1] for x in ids[i:i + 50])
        d = get(API, {"filter": f"openalex:{chunk}", "per-page": 50, "select": FIELDS})
        out += d["results"]
        time.sleep(PAUSE)
    return out


def abstract(inv):
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos)


def slim(w):
    loc = (w.get("primary_location") or {}).get("source") or {}
    auth = w.get("authorships") or []
    first = (auth[0]["author"]["display_name"] if auth else "") + (" et al." if len(auth) > 1 else "")
    return dict(id=w["id"], doi=w.get("doi"), title=w.get("title"), year=w.get("publication_year"),
                venue=loc.get("display_name"), type=w.get("type"), cited_by=w.get("cited_by_count"),
                authors=first, abstract=abstract(w.get("abstract_inverted_index")), found_by=[])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hits, log = {}, []

    def add(works, tag):
        for w in works:
            h = hits.setdefault(w["id"], slim(w))
            if tag not in h["found_by"]:
                h["found_by"].append(tag)

    for tag, q in SEARCHES.items():
        works, n = fetch_all(f"title_and_abstract.search:{q}")
        add(works, tag)
        log.append(dict(source=tag, query=q, total=n, retrieved=len(works)))
        print(f"{tag}: {n} total, {len(works)} retrieved")

    for tag, doi in ANCHORS.items():
        a = get(f"{API}/doi:{doi}", {"select": FIELDS})
        add([a], f"anchor:{tag}")
        refs = fetch_ids(a.get("referenced_works") or [])
        add(refs, f"backward:{tag}")
        cites, n = fetch_all(f"cites:{a['id'].rsplit('/', 1)[-1]}")
        add(cites, f"forward:{tag}")
        log.append(dict(source=tag, doi=doi, openalex=a["id"], backward=len(refs), forward_total=n,
                        forward_retrieved=len(cites)))
        print(f"{tag}: {len(refs)} references, {n} citing works")

    (OUT / "hits.json").write_text(json.dumps(list(hits.values()), indent=1, ensure_ascii=False))
    (OUT / "search_log.json").write_text(json.dumps(
        dict(date=time.strftime("%Y-%m-%d"), api=API, log=log, unique_hits=len(hits)), indent=1))
    print(f"{len(hits)} unique works -> {OUT}")


if __name__ == "__main__":
    main()
