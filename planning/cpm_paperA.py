#!/usr/bin/env python3
"""Critical-path schedule for Paper A.

Edit the ACTIVITIES list below, then run:

    python3 planning/cpm_paperA.py

The script:
  1. runs the CPM forward and backward passes (ES, EF, LS, LF, total float),
  2. builds a single-researcher schedule (one Effort activity at a time;
     Wait/HPC activities run in parallel; the ready activity with the smallest LS goes first),
  3. rewrites the precedence table and the AON Mermaid diagram in
     planning/PAPER_A_SCHEDULE.md between the BEGIN/END GENERATED markers,
  4. prints the summary numbers.

The prose in PAPER_A_SCHEDULE.md (§2, which quotes the summary numbers) is NOT regenerated.
Update it by hand from the printed summary.

Conventions:
  type  E = Effort (needs your time), W = Wait/HPC (elapsed time only), M = Milestone (0 weeks)
  dur   calendar weeks at 0.5 FTE
  pred  finish-to-start predecessors
"""
import math
import pathlib
import re

# (id, name, type, duration_weeks, [predecessors], phase)
ACTIVITIES = [
    ("A01", "Novelty searches and citation chasing", "E", 3, [], "Setup"),
    ("A02", "Download datasets; start data dictionary", "E", 1, [], "Setup"),
    ("A03", "Contact data owners (IFP, NCF)", "E", 1, [], "Setup"),
    ("A04", "Await replies; agree authorship terms", "W", 6, ["A03"], "Setup"),
    ("A05", "NBA/DSI clarification (query and wait)", "W", 6, [], "Setup"),
    ("A06", "HPC allocation proposal", "E", 1, [], "Setup"),
    ("A07", "Await HPC allocation", "W", 6, ["A06"], "Setup"),
    ("A08", "Repo, lockfiles, container, Snakemake, registry", "E", 2, [], "Setup"),
    ("GA1", "Gate A1: novelty", "M", 0, ["A01"], "Setup"),
    ("GP0", "Gate P0: permissions, NBA/DSI, HPC", "M", 0, ["A04", "A05", "A07"], "Setup"),
    ("A09", "Data harmonisation; taxonomic backbone", "E", 3, ["A02"], "Data"),
    ("A10", "Observation-process audit", "E", 2, ["A09", "A04"], "Data"),
    ("GA2", "Gate A2: data audit", "M", 0, ["A10"], "Data"),
    ("A11", "Trait compilation; guild definition", "E", 2, ["A09"], "Data"),
    ("A12", "Climate: download; plot-scale station validation", "E", 3, ["A08"], "Climate"),
    ("A13", "Climate: PET, deficit metrics, hindcast series", "E", 2, ["A12"], "Climate"),
    ("A14", "Climate: GCM selection; delta-change projections", "E", 3, ["A13"], "Climate"),
    ("A15", "Stage-1 prototype; choose Turing.jl or brms", "E", 1, ["GA2", "A11", "GA1"], "Stage 1"),
    ("A16", "Stage-1 fits: growth and survival, M0-M3", "E", 4, ["A15", "A13", "GP0"], "Stage 1"),
    ("A17", "Stage-1 checks: PPC, PSIS-LOO, leave-one-interval-out", "E", 2, ["A16"], "Stage 1"),
    ("A18", "IBM implementation (state, processes)", "E", 4, ["A08", "A11", "GA2", "GA1"], "IBM"),
    ("A19", "Observation model and unit tests", "E", 2, ["A18"], "IBM"),
    ("A20", "Runtime benchmark; HPC job arrays", "E", 1, ["A19", "A07"], "IBM"),
    ("A21", "Priors table; prior-predictive checks", "E", 1, ["A17", "A19"], "IBM"),
    ("A22", "ODD draft", "E", 1, ["A19"], "IBM"),
    ("A23", "Pre-registration (OSF)", "E", 1, ["A17", "A21", "GA1"], "Inference"),
    ("A24", "Identifiability and detectability runs (HPC)", "W", 2, ["A20", "A21", "A23"], "Inference"),
    ("A25", "Identifiability analysis: SBC, contraction, MDE", "E", 2, ["A24"], "Inference"),
    ("GA3", "Gate A3: identifiability", "M", 0, ["A25"], "Inference"),
    ("A26", "NPE training simulations (HPC)", "W", 2, ["GA3"], "Inference"),
    ("A27", "NPE ensemble training; synthetic diagnostics", "E", 3, ["A26"], "Inference"),
    ("A28", "Misspecification check on real data", "E", 1, ["A27"], "Inference"),
    ("GA4", "Gate A4: misspecification", "M", 0, ["A28"], "Inference"),
    ("A29", "Inference check: no-cut NPE vs Stage 1", "E", 2, ["A27", "A17"], "Inference"),
    ("A30", "Temporal hold-out validation", "E", 2, ["GA4"], "Validation"),
    ("A31", "Leave-one-site-out transfer and diagnostics", "E", 2, ["GA4"], "Validation"),
    ("A32", "Within-plot spatial blocks", "E", 1, ["GA4"], "Validation"),
    ("A33", "96-site space-for-time check", "E", 1, ["GA4", "A13"], "Validation"),
    ("A34", "Final joint fit (all data)", "E", 1, ["A30", "A31"], "Projections"),
    ("A35", "Projection ensemble runs (HPC)", "W", 2, ["A34", "A14"], "Projections"),
    ("A36", "Uncertainty partition; prior vs posterior; extrapolation flags", "E", 2, ["A35"], "Projections"),
    ("A37", "Figures and tables", "E", 2, ["A36", "A32", "A33", "A29"], "Writing"),
    ("A38", "Draft introduction and methods", "E", 2, ["A23", "A22"], "Writing"),
    ("A39", "Draft results and discussion", "E", 3, ["A37", "A38"], "Writing"),
    ("A40", "Co-author review", "W", 4, ["A39"], "Writing"),
    ("A41", "Archive: code, container, data, TRACE document", "E", 2, ["A37"], "Writing"),
    ("A42", "Revise, preprint, submit", "E", 2, ["A40", "A41"], "Writing"),
    ("MSUB", "Submission", "M", 0, ["A42"], "Writing"),
]

PHASES = ["Setup", "Data", "Climate", "Stage 1", "IBM", "Inference", "Validation", "Projections", "Writing"]
WEEKS_PER_MONTH = 4.345
MD_FILE = pathlib.Path(__file__).with_name("PAPER_A_SCHEDULE.md")


def build(activities):
    ids = [a[0] for a in activities]
    A = {a[0]: dict(id=a[0], name=a[1], type=a[2], d=a[3], pred=list(a[4]), phase=a[5], succ=[])
         for a in activities}
    assert len(A) == len(ids), "duplicate activity IDs"
    for a in A.values():
        assert a["type"] in "EWM", (a["id"], a["type"])
        assert a["phase"] in PHASES, (a["id"], a["phase"])
        assert a["type"] != "M" or a["d"] == 0, (a["id"], "milestones have zero duration")
        for p in a["pred"]:
            assert p in A, f"{a['id']}: unknown predecessor {p}"
            A[p]["succ"].append(a["id"])
    # Topological order (Kahn's algorithm); catches cycles.
    indeg = {i: len(A[i]["pred"]) for i in ids}
    queue = [i for i in ids if indeg[i] == 0]
    topo = []
    while queue:
        i = queue.pop(0)
        topo.append(i)
        for s in A[i]["succ"]:
            indeg[s] -= 1
            if indeg[s] == 0:
                queue.append(s)
    assert len(topo) == len(ids), "dependency cycle detected"
    return ids, topo, A


def cpm(topo, A):
    for i in topo:  # forward pass
        a = A[i]
        a["ES"] = max((A[p]["EF"] for p in a["pred"]), default=0)
        a["EF"] = a["ES"] + a["d"]
    T = max(a["EF"] for a in A.values())
    for i in reversed(topo):  # backward pass
        a = A[i]
        a["LF"] = min((A[s]["LS"] for s in a["succ"]), default=T)
        a["LS"] = a["LF"] - a["d"]
        a["TF"] = a["LS"] - a["ES"]
    return T


def level(ids, A):
    """One Effort activity at a time; Wait/HPC unlimited; milestones instantaneous."""
    done, start, running = {}, {}, {}
    busy_until, t = 0, 0
    remaining = set(ids)
    while remaining:
        progressed = True
        while progressed:
            progressed = False
            ready = [i for i in ids if i in remaining and i not in running
                     and all(p in done and done[p] <= t for p in A[i]["pred"])]
            for i in ready:
                if A[i]["type"] == "M":
                    start[i] = done[i] = t
                    remaining.discard(i)
                    progressed = True
                elif A[i]["type"] == "W":
                    start[i], running[i] = t, t + A[i]["d"]
                    progressed = True
            ready_e = sorted((i for i in ready if A[i]["type"] == "E"), key=lambda i: (A[i]["LS"], i))
            if ready_e and busy_until <= t:
                i = ready_e[0]
                start[i], running[i] = t, t + A[i]["d"]
                busy_until = running[i]
                progressed = True
        t += 1
        for i, f in list(running.items()):
            if f <= t:
                done[i] = f
                remaining.discard(i)
                del running[i]
        assert t < 10_000, "levelling did not terminate"
    for i in ids:
        A[i]["LvS"], A[i]["LvF"] = start[i], done[i]
    return max(done.values())


def month(week):
    return max(1, math.ceil(week / WEEKS_PER_MONTH - 1e-9))


def table_md(ids, A):
    kind = {"E": "Effort", "W": "Wait/HPC", "M": "Milestone"}
    rows = ["| ID | Activity | Type | Dur (wk) | Predecessors | ES | EF | LS | LF | Float | Critical "
            "| Levelled start–finish (wk) | Levelled finish month |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for ph in PHASES:
        rows.append(f"| | **{ph}** | | | | | | | | | | | |")
        for i in ids:
            a = A[i]
            if a["phase"] != ph:
                continue
            name = f"**{a['name']}**" if a["type"] == "M" else a["name"]
            rows.append(
                f"| {i} | {name} | {kind[a['type']]} | {a['d']} | {', '.join(a['pred']) or '–'} "
                f"| {a['ES']} | {a['EF']} | {a['LS']} | {a['LF']} | {a['TF']} | {'●' if a['TF'] == 0 else ''} "
                f"| {a['LvS']}–{a['LvF']} | M{month(a['LvF'])} |")
    return "\n".join(rows)


def diagram_md(ids, A):
    L = ["```mermaid", "flowchart TD"]
    for ph in PHASES:
        L.append(f'  subgraph {ph.replace(" ", "")}["{ph}"]')
        for i in ids:
            a = A[i]
            if a["phase"] != ph:
                continue
            lab = f"{i} · {a['name']}".replace(";", ",").replace('"', "'")
            if a["type"] == "M":
                L.append(f'    {i}{{"{lab}"}}')
            elif a["type"] == "W":
                L.append(f'    {i}(["{lab}<br/>{a["d"]} wk"])')
            else:
                L.append(f'    {i}["{lab}<br/>{a["d"]} wk"]')
        L.append("  end")
    crit_edges, n = [], 0
    for i in ids:
        for p in A[i]["pred"]:
            L.append(f"  {p} --> {i}")
            if A[i]["TF"] == 0 and A[p]["TF"] == 0 and A[p]["EF"] == A[i]["ES"]:
                crit_edges.append(str(n))
            n += 1
    L += ["  classDef effort fill:#e8f0fe,stroke:#4a6fa5,color:#111",
          "  classDef wait fill:#f3f3f3,stroke:#888,color:#111,stroke-dasharray:4 3",
          "  classDef gate fill:#fff4d6,stroke:#b8860b,color:#111",
          "  classDef critical stroke:#c0392b,stroke-width:3px"]
    for t, c in (("E", "effort"), ("W", "wait"), ("M", "gate")):
        L.append(f"  class {','.join(i for i in ids if A[i]['type'] == t)} {c}")
    L.append(f"  class {','.join(i for i in ids if A[i]['TF'] == 0)} critical")
    if crit_edges:
        L.append(f"  linkStyle {','.join(crit_edges)} stroke:#c0392b,stroke-width:3px")
    L.append("```")
    return "\n".join(L)


def replace_block(text, tag, body):
    pat = re.compile(rf"(<!-- BEGIN GENERATED {tag}[^\n]*-->\n).*?(\n<!-- END GENERATED {tag} -->)", re.S)
    new, n = pat.subn(lambda m: m.group(1) + body + m.group(2), text)
    assert n == 1, f"marker for {tag} not found exactly once in {MD_FILE.name}"
    return new


def main():
    ids, topo, A = build(ACTIVITIES)
    T = cpm(topo, A)
    TL = level(ids, A)
    text = MD_FILE.read_text()
    text = replace_block(text, "TABLE", table_md(ids, A))
    text = replace_block(text, "DIAGRAM", diagram_md(ids, A))
    MD_FILE.write_text(text)

    effort = sum(a["d"] for a in A.values() if a["type"] == "E")
    print(f"Total effort:              {effort} weeks ({effort / WEEKS_PER_MONTH:.1f} months)")
    print(f"CPM duration:              {T} weeks ({T / WEEKS_PER_MONTH:.1f} months)")
    print(f"Levelled duration:         {TL} weeks -> submission in M{month(TL)}")
    print("Critical path:            ", " -> ".join(i for i in topo if A[i]["TF"] == 0))
    print("Milestones (levelled):    ",
          ", ".join(f"{i} wk{A[i]['LvF']} (M{month(A[i]['LvF'])})" for i in ids if A[i]["type"] == "M"))
    print(f"Updated {MD_FILE}")


if __name__ == "__main__":
    main()
