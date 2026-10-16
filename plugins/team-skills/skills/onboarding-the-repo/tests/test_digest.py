import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "digest.py"
sys.path.insert(0, str(SKILL_DIR))
import digest as dg  # noqa: E402

ROOT = "C:/work/payments-api"
REPORT = '''# Graph Report

### Community 0 - "Auth & Sessions"
Cohesion: 0.71
Nodes (3): AuthService, Session, login

### Community 1 - "Ledger"
Cohesion: 0.40
Nodes (2): Ledger, Entry
'''


def node(i, comm, f=None, **kw):
    n = {"id": i, "label": i, "community": comm}
    if f:
        n["source_file"] = f
    n.update(kw)
    return n


def sample_graph():
    return {
        "nodes": [
            node("AuthService", 0, "C:\\work\\payments-api\\src\\auth\\service.ts"),
            node("Session", 0, "src/auth/session.ts"),
            node("login", 0, "src/auth/service.ts"),
            node("Ledger", 1, "./src/ledger/ledger.ts"),
            node("Entry", 1, "src/ledger/entry.ts"),
            node("Orphan", None, "src/misc.ts"),
            node("Mailer", 2, "src/notify/mailer.ts", community_name="Notifications"),
        ],
        "links": [
            {"source": "AuthService", "target": "Session"},
            {"source": "AuthService", "target": "login"},
            {"source": "AuthService", "target": "Ledger"},
            {"source": "login", "target": "Entry"},
            {"source": "Ledger", "target": "Entry"},
            {"source": "Orphan", "target": "AuthService"},
            {"source": "Mailer", "target": "AuthService"},
        ],
        "built_at_commit": "a1b2c3d4e5f6",
    }


class DigestTests(unittest.TestCase):
    def setUp(self):
        self.d = dg.digest(sample_graph(), REPORT, ROOT,
                           commit="a1b2c3d4e5f6", today=date(2026, 10, 12))

    def comm(self, cid):
        return next(c for c in self.d["graph"]["communities"] if c["id"] == cid)

    def test_labels_and_cohesion_from_report(self):
        self.assertEqual(self.comm(0)["label"], "Auth & Sessions")
        self.assertEqual(self.comm(0)["cohesion"], 0.71)

    def test_label_falls_back_to_community_name(self):
        self.assertEqual(self.comm(2)["label"], "Notifications")
        self.assertIsNone(self.comm(2)["cohesion"])

    def test_unclustered_nodes_ignored(self):
        self.assertEqual(sum(c["size"] for c in self.d["graph"]["communities"]), 6)
        self.assertEqual(self.d["meta"]["graphStats"]["communities"], 3)

    def test_top_files_relative_forward_slash_ranked(self):
        self.assertEqual(self.comm(0)["topFiles"],
                         ["src/auth/service.ts", "src/auth/session.ts"])
        self.assertEqual(self.comm(1)["topFiles"],
                         ["src/ledger/entry.ts", "src/ledger/ledger.ts"])

    def test_cross_community_links_weighted_and_self_links_dropped(self):
        self.assertEqual(self.d["graph"]["links"], [
            {"from": 0, "to": 1, "weight": 2},
            {"from": 0, "to": 2, "weight": 1},
        ])

    def test_tiny_links_dropped(self):
        nodes = ([node(f"a{i}", 0) for i in range(100)]
                 + [node(f"b{i}", 1) for i in range(100)] + [node("c0", 2)])
        links = ([{"source": f"a{i}", "target": f"b{i}"} for i in range(100)]
                 + [{"source": "a0", "target": "c0"}])
        d = dg.digest({"nodes": nodes, "links": links}, "", ROOT)
        self.assertEqual([(l["from"], l["to"]) for l in d["graph"]["links"]], [(0, 1)])

    def test_caps(self):
        nodes, links = [], []
        for c in range(50):
            for k in range(c + 1):
                nodes.append(node(f"n{c}_{k}", c, f"src/c{c}/f{k}.ts"))
        for i in range(20):
            links.append({"source": "n49_0", "target": f"n49_{i + 1}"})
        d = dg.digest({"nodes": nodes, "links": links}, "", ROOT)
        comms = d["graph"]["communities"]
        self.assertEqual(len(comms), 40)
        self.assertEqual(comms[0]["id"], 49)
        self.assertNotIn(0, [c["id"] for c in comms])
        self.assertEqual(len(comms[0]["topFiles"]), 8)
        self.assertEqual(len(d["graph"]["godNodes"]), 15)
        self.assertEqual(d["graph"]["godNodes"][0]["id"], "n49_0")
        self.assertEqual(d["meta"]["graphStats"]["communities"], 50)

    def test_god_nodes(self):
        self.assertEqual(self.d["graph"]["godNodes"][0], {
            "id": "AuthService", "label": "AuthService",
            "file": "src/auth/service.ts", "community": 0, "degree": 5,
        })

    def test_meta_and_empty_sections(self):
        m = self.d["meta"]
        self.assertEqual(m["repo"], "payments-api")
        self.assertEqual(m["commit"], "a1b2c3d")
        self.assertEqual(m["generatedAt"], "2026-10-12")
        self.assertEqual(m["scope"], ".")
        self.assertFalse(m["graphStale"])
        self.assertEqual(m["graphStats"], {"nodes": 7, "edges": 7, "communities": 3})
        self.assertEqual(self.d["architecture"], {"summary": "", "communities": {}})
        self.assertEqual(self.d["runLocally"],
                         {"prerequisites": [], "steps": [], "unknowns": []})
        for k in ("whereThingsLive", "flows", "conventions", "glossary"):
            self.assertEqual(self.d[k], [])


class ScopeTests(unittest.TestCase):
    def graph(self):
        return {"nodes": [
            node("A", 0, "auth/service.ts"),
            node("B", 0, "src/x.ts"),
            node("C", 0, "C:\\work\\payments-api\\src\\y.ts"),
        ], "links": [{"source": "A", "target": "B"}, {"source": "A", "target": "C"}]}

    def run_scope(self, scope):
        return dg.digest(self.graph(), "", ROOT, scope=scope, today=date(2026, 10, 12))

    def test_scope_prefixes_relative_paths(self):
        d = self.run_scope("src")
        self.assertEqual(sorted(d["graph"]["communities"][0]["topFiles"]),
                         ["src/auth/service.ts", "src/x.ts", "src/y.ts"])
        god = {g["id"]: g["file"] for g in d["graph"]["godNodes"]}
        self.assertEqual(god["A"], "src/auth/service.ts")
        self.assertEqual(god["B"], "src/x.ts")
        self.assertEqual(god["C"], "src/y.ts")

    def test_scope_dot_leaves_paths_unchanged(self):
        d = self.run_scope(".")
        self.assertEqual(sorted(d["graph"]["communities"][0]["topFiles"]),
                         ["auth/service.ts", "src/x.ts", "src/y.ts"])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              capture_output=True, text=True)

    def test_missing_graph_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_cli(tmp, Path(tmp) / "out.json")
            self.assertEqual(r.returncode, 2)
            self.assertIn("not found", r.stderr)

    def test_empty_graph_exits_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "graphify-out").mkdir()
            (Path(tmp) / "graphify-out" / "graph.json").write_text('{"nodes":[],"links":[]}')
            r = self.run_cli(tmp, Path(tmp) / "out.json")
            self.assertEqual(r.returncode, 3)

    def test_writes_skeleton_with_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "graphify-out"
            out_dir.mkdir()
            (out_dir / "graph.json").write_text(json.dumps(sample_graph()), encoding="utf-8")
            (out_dir / "GRAPH_REPORT.md").write_text(REPORT, encoding="utf-8")
            out = out_dir / "onboarding" / "data.json"
            r = self.run_cli(tmp, out, "--scope", "src", "--stale")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(data["meta"]["scope"], "src")
            self.assertTrue(data["meta"]["graphStale"])
            self.assertEqual(data["meta"]["commit"], "a1b2c3d")
            self.assertEqual(len(data["graph"]["communities"]), 3)

    def test_check_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = self.run_cli("--check-stale", tmp)
            self.assertEqual((r.returncode, r.stdout.strip()), (1, "stale"))
            out_dir = Path(tmp) / "graphify-out"
            out_dir.mkdir()
            (out_dir / "graph.json").write_text(json.dumps(sample_graph()))
            r = self.run_cli("--check-stale", tmp)
            self.assertEqual((r.returncode, r.stdout.strip()), (0, "fresh"))
            (out_dir / ".needs_update").write_text("")
            r = self.run_cli("--check-stale", tmp)
            self.assertEqual((r.returncode, r.stdout.strip()), (1, "stale"))


if __name__ == "__main__":
    unittest.main()
