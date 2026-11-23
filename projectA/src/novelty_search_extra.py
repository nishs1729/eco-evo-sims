#!/usr/bin/env python3
"""A01 supplementary novelty search: Crossref and Semantic Scholar.

Complements novelty_search.py (OpenAlex). Crossref covers DOIs registered by
Indian publishers (Indian Forester, Current Science, ...) that OpenAlex indexes
patchily; Semantic Scholar supports Boolean bulk search.

Crossref has no Boolean search, so it runs simple keyword queries and the same
Boolean logic is applied locally to title (+ abstract where available).
New works (not already in results/novelty/hits.json, matched by DOI or
normalised title) are written to results/novelty/extra_new_hits.json.

Scopus, Web of Science and Google Scholar were deliberately not searched
(decision 2026-11-23, docs/decisions.md); the A01 search is closed.

Optional API key (read from an environment variable, never stored):
  S2_API_KEY       Semantic Scholar (higher rate limit)

Usage:  python3 projectA/src/novelty_search_extra.py
"""
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.parse
import urllib.request

OUT = pathlib.Path(__file__).resolve().parents[1] / "results" / "novelty"
UA = {"User-Agent": "eco-evo-sims-novelty-search/0.1 (research literature search)"}

# Simple keyword queries for Crossref (relevance-ranked; top ROWS kept per query).
CROSSREF_QUERIES = [
    "Uppangala",
    "Western Ghats tree mortality", "Western Ghats tree growth", "Western Ghats tree recruitment",
    "Western Ghats forest dynamics", "Western Ghats permanent plot", "Western Ghats drought trees",
    "Western Ghats forest climate change", "Anamalai rainforest plot", "Kodagu evergreen forest",
    "Karnataka evergreen forest dynamics", "Kerala evergreen forest tree population dynamics",
    "India tropical forest tree mortality drought", "India forest demographic model climate",
    "tropical forest individual-based model Bayesian calibration",
    "tropical forest model approximate Bayesian computation",
    "forest model simulation-based inference neural posterior",
]
ROWS = 300

# Semantic Scholar bulk-search Boolean queries (+ = AND, | = OR, quotes = phrase).
S2_QUERIES = {
    "S2_WG_demography_climate": '"Western Ghats" + (mortality | growth | recruitment | demography | dynamics) + (drought | climate | rainfall | "dry season")',
    "S3_Uppangala": "Uppangala",
    "S5_WG_plots": '"Western Ghats" + ("permanent plot" | "permanent sample plot" | "long-term plot" | "forest dynamics" | census)',
    "S1_model_calibration": '("tropical forest" | rainforest) + ("individual-based" | "forest model" | FORMIND | TROLL) + (calibration | "approximate Bayesian" | "simulation-based inference" | "neural posterior")',
}

# Local relevance filters (title + abstract).
INDIA = re.compile(r"India|Indian|Western Ghats|Ghats|Karnataka|Kerala|Tamil Nadu|Kodagu|Coorg|Anamalai|Uppangala|Nilgiri|South Asia|Sri Lanka", re.I)
DEMOG = re.compile(r"mortality|growth|recruit|demograph|dynamics|census|permanent (sample )?plot|drought|water deficit|rainfall|climate|tree.ring|dendro|model", re.I)
FOREST = re.compile(r"tree|forest|woody|stem|stand", re.I)
MODEL = re.compile(r"individual-based|forest model|gap model|simulator|FORMIND|TROLL|perfect plasticity|demographic model", re.I)
CALIB = re.compile(r"calibrat|Bayesian|approximate Bayesian|simulation-based inference|neural posterior|inverse model|parameteri[sz]", re.I)


def get_json(url, headers=None, tries=6):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def norm_title(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:120]


def relevant(title, abstract):
    t = f"{title} {abstract}"
    regional = INDIA.search(t) and DEMOG.search(t) and FOREST.search(t)
    methods = FOREST.search(t) and MODEL.search(t) and CALIB.search(t)
    return bool(regional or methods)


def crossref():
    out = {}
    for q in CROSSREF_QUERIES:
        params = {"query.bibliographic": q, "rows": ROWS,
                  "select": "DOI,title,issued,container-title,author,abstract,type"}
        d = get_json("https://api.crossref.org/works?" + urllib.parse.urlencode(params))
        for it in d["message"]["items"]:
            title = (it.get("title") or [""])[0]
            abstract = re.sub(r"<[^>]+>", " ", it.get("abstract") or "")
            if not relevant(title, abstract):
                continue
            doi = (it.get("DOI") or "").lower()
            year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
            auth = it.get("author") or []
            first = (auth[0].get("family", "") if auth else "") + (" et al." if len(auth) > 1 else "")
            rec = out.setdefault(doi or norm_title(title), dict(
                doi=f"https://doi.org/{doi}" if doi else None, title=title, year=year,
                venue=(it.get("container-title") or [""])[0], type=it.get("type"), authors=first,
                abstract=abstract.strip(), found_by=[]))
            rec["found_by"].append(f"crossref:{q}")
        print(f"crossref '{q}': {len(d['message']['items'])} retrieved, total {d['message']['total-results']}")
        time.sleep(1)
    return out


def semantic_scholar():
    out = {}
    headers = {"x-api-key": os.environ["S2_API_KEY"]} if os.environ.get("S2_API_KEY") else {}
    for tag, q in S2_QUERIES.items():
        params = {"query": q, "fields": "title,year,venue,externalIds,abstract,authors,publicationTypes"}
        token, n = None, 0
        while True:
            if token:
                params["token"] = token
            d = get_json("https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(params), headers)
            for p in d.get("data") or []:
                title, abstract = p.get("title") or "", p.get("abstract") or ""
                n += 1
                if not relevant(title, abstract):
                    continue
                doi = ((p.get("externalIds") or {}).get("DOI") or "").lower()
                auth = p.get("authors") or []
                first = (auth[0]["name"] if auth else "") + (" et al." if len(auth) > 1 else "")
                rec = out.setdefault(doi or norm_title(title), dict(
                    doi=f"https://doi.org/{doi}" if doi else None, title=title, year=p.get("year"),
                    venue=p.get("venue"), type=",".join(p.get("publicationTypes") or []), authors=first,
                    abstract=abstract, found_by=[]))
                rec["found_by"].append(f"s2:{tag}")
            token = d.get("token")
            time.sleep(1.5)
            if not token or n >= 3000:
                break
        print(f"semantic scholar {tag}: {d.get('total')} total, {n} scanned")
    return out


def main():
    known = json.loads((OUT / "hits.json").read_text())
    known_doi = {(h.get("doi") or "").lower() for h in known if h.get("doi")}
    known_title = {norm_title(h.get("title")) for h in known}
    log, merged = [], {}
    for name, fn in (("crossref", crossref), ("semantic_scholar", semantic_scholar)):
        try:
            res = fn()
        except Exception as e:  # keep going if one source fails
            print(f"{name} failed: {e}")
            log.append(dict(source=name, error=str(e)))
            continue
        log.append(dict(source=name, relevant=len(res)))
        for k, r in res.items():
            m = merged.setdefault(norm_title(r["title"]) or k, r)
            if m is not r:
                m["found_by"] += [t for t in r["found_by"] if t not in m["found_by"]]
    new = [r for r in merged.values()
           if (r["doi"] or "").lower() not in known_doi and norm_title(r["title"]) not in known_title]
    (OUT / "extra_new_hits.json").write_text(json.dumps(new, indent=1, ensure_ascii=False))
    (OUT / "extra_search_log.json").write_text(json.dumps(dict(
        date=time.strftime("%Y-%m-%d"), crossref_queries=CROSSREF_QUERIES, rows_per_query=ROWS,
        s2_queries=S2_QUERIES, log=log, relevant_total=len(merged), new_vs_openalex=len(new)), indent=1))
    print(f"{len(merged)} relevant after local filter; {len(new)} not already found via OpenAlex")


if __name__ == "__main__":
    main()
