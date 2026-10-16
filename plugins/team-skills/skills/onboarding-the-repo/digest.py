#!/usr/bin/env python3
"""Condense a graphify graph into the onboarding page's data.json skeleton.

Usage:
  python digest.py <repo_root> <out_path> [--scope DIR] [--stale]
  python digest.py --check-stale <repo_root>

Reads <repo_root>/graphify-out/graph.json (and GRAPH_REPORT.md if present).
Standard library only; no LLM.
"""
import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

MAX_COMMUNITIES = 40
MAX_TOP_FILES = 8
MAX_GOD_NODES = 15
MIN_LINK_RATIO = 0.02

_COMMUNITY_RE = re.compile(r'^### Community (\d+) - "(.*)"\s*\nCohesion: ([0-9.]+)', re.M)


def parse_report(text):
    """Map community id -> {"label", "cohesion"} from GRAPH_REPORT.md."""
    return {int(m.group(1)): {"label": m.group(2), "cohesion": float(m.group(3))}
            for m in _COMMUNITY_RE.finditer(text or "")}


def norm_path(path, root, scope="."):
    """Repo-relative, forward-slash path; None for empty input.

    graphify stores source_file relative to the folder it scanned, so with a
    narrowed scope, relative paths get the scope prefixed. Absolute paths under
    the repo root are already repo-relative once the root is stripped.
    """
    if not path:
        return None
    p = str(path).replace("\\", "/")
    r = str(root).replace("\\", "/").rstrip("/") + "/"
    absolute = p.lower().startswith(r.lower())
    if absolute:
        p = p[len(r):]
    if p.startswith("./"):
        p = p[2:]
    if not absolute and scope not in (".", ""):
        prefix = scope.replace("\\", "/").strip("/") + "/"
        if not p.startswith(prefix):
            p = prefix + p
    return p


def empty_sections():
    return {
        "architecture": {"summary": "", "communities": {}},
        "runLocally": {"prerequisites": [], "steps": [], "unknowns": []},
        "whereThingsLive": [],
        "flows": [],
        "conventions": [],
        "glossary": [],
    }


def digest(graph, report_text, root, *, commit=None, today=None, scope=".", stale=False):
    nodes = graph.get("nodes", [])
    links = graph.get("links", graph.get("edges", []))
    report = parse_report(report_text)

    node_comm, members = {}, defaultdict(list)
    for n in nodes:
        cid = n.get("community")
        if cid is None:
            continue
        node_comm[n["id"]] = cid
        members[cid].append(n)

    degree, pair_weight = Counter(), Counter()
    for link in links:
        s, t = link.get("source"), link.get("target")
        degree[s] += 1
        degree[t] += 1
        cs, ct = node_comm.get(s), node_comm.get(t)
        if cs is not None and ct is not None and cs != ct:
            pair_weight[tuple(sorted((cs, ct)))] += 1

    kept = sorted(members, key=lambda c: (-len(members[c]), c))[:MAX_COMMUNITIES]
    kept_set = set(kept)

    communities = []
    for cid in kept:
        ms = members[cid]
        info = report.get(cid, {})
        label = info.get("label") or next(
            (m["community_name"] for m in ms if m.get("community_name")), f"Community {cid}")
        file_score = Counter()
        for m in ms:
            f = norm_path(m.get("source_file"), root, scope)
            if f:
                file_score[f] += degree[m["id"]] + 1
        top = sorted(file_score, key=lambda f: (-file_score[f], f))[:MAX_TOP_FILES]
        communities.append({"id": cid, "label": label, "cohesion": info.get("cohesion"),
                            "size": len(ms), "topFiles": top})

    kept_pairs = {p: w for p, w in pair_weight.items()
                  if p[0] in kept_set and p[1] in kept_set}
    max_w = max(kept_pairs.values(), default=0)
    out_links = [{"from": a, "to": b, "weight": w}
                 for (a, b), w in sorted(kept_pairs.items(), key=lambda kv: (-kv[1], kv[0]))
                 if w >= max_w * MIN_LINK_RATIO]

    by_id = {n["id"]: n for n in nodes}
    gods = sorted((i for i in degree if i in by_id),
                  key=lambda i: (-degree[i], str(i)))[:MAX_GOD_NODES]
    god_nodes = [{"id": i, "label": by_id[i].get("label", i),
                  "file": norm_path(by_id[i].get("source_file"), root, scope),
                  "community": node_comm.get(i), "degree": degree[i]} for i in gods]

    data = {
        "meta": {
            "repo": Path(root).resolve().name,
            "commit": (commit or "")[:7] or None,
            "generatedAt": (today or date.today()).isoformat(),
            "scope": scope,
            "graphStale": stale,
            "graphStats": {"nodes": len(nodes), "edges": len(links),
                           "communities": len(members)},
        },
        "graph": {"communities": communities, "links": out_links, "godNodes": god_nodes},
    }
    data.update(empty_sections())
    return data


def _git(root, *args):
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                              text=True, check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def is_stale(root):
    out = Path(root) / "graphify-out"
    graph = out / "graph.json"
    if not graph.exists() or (out / ".needs_update").exists():
        return True
    ts = _git(root, "log", "-1", "--format=%ct")
    return bool(ts) and int(ts) > graph.stat().st_mtime


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the onboarding data.json skeleton.")
    ap.add_argument("--check-stale", action="store_true",
                    help="print stale/fresh for the repo's graph and exit 1/0")
    ap.add_argument("repo_root")
    ap.add_argument("out_path", nargs="?")
    ap.add_argument("--scope", default=".")
    ap.add_argument("--stale", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.repo_root)

    if a.check_stale:
        stale = is_stale(root)
        print("stale" if stale else "fresh")
        return 1 if stale else 0
    if not a.out_path:
        ap.error("out_path is required unless --check-stale is given")

    graph_path = root / "graphify-out" / "graph.json"
    if not graph_path.exists():
        print(f"ERROR: {graph_path} not found - build the graph with graphify first.",
              file=sys.stderr)
        return 2
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    if not graph.get("nodes"):
        print("ERROR: graph.json has no nodes.", file=sys.stderr)
        return 3
    report_path = root / "graphify-out" / "GRAPH_REPORT.md"
    report = report_path.read_text(encoding="utf-8") if report_path.exists() else ""

    commit = graph.get("built_at_commit") or _git(root, "rev-parse", "HEAD")
    data = digest(graph, report, root, commit=commit, scope=a.scope, stale=a.stale)

    out = Path(a.out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    g = data["graph"]
    print(f"Digest: {len(g['communities'])} communities, {len(g['links'])} links, "
          f"{len(g['godNodes'])} god nodes -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
