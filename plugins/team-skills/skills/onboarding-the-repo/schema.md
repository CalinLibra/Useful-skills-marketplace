# data.json contract

`digest.py` writes `meta` and `graph`. **Do not edit them.** Claude fills in
every other section. The reference example is
`examples/data-full.json`; match its field shape exactly. The example is abbreviated: follow the counts given in each section below, not the example's counts.
The jsonc snippets below are illustrative (`a | b` means one of the listed values); example names in data-full.json are made up — real flow nodes must exist in graph.json.

## Rules for every authored item

- `source`: where the claim comes from. Use a repo-relative file path
  (`README.md`, `src/auth/service.ts`), `graph` (from graph.json /
  GRAPH_REPORT.md), `graphify path`, `graphify query`, or `team` (a team
  standard such as a skill).
- `confidence`: `verified` when the item was read directly in a file or is an
  EXTRACTED graph fact. `inferred` for everything else. When in doubt, use `inferred`.
- Never invent a command, file path, env var or node. If you could not
  find it, it goes in `runLocally.unknowns` or is left out.
- Plain text only. The page renders everything as text, so do not write HTML or Markdown.

## Sections

### architecture
```jsonc
{
  "summary": "3-5 sentences: what the system does and its main parts.",
  "communities": {
    "<community id as string>": {
      "description": "1-3 sentences: what this subsystem is responsible for.",
      "entryPoints": ["src/auth/routes.ts"],      // files/symbols a reader opens first
      "layer": "ui" | "service" | "data" | "infra", // always inferred
      "source": "graph", "confidence": "verified" | "inferred"
    }
  }
}
```
Write an entry for **every** id in `graph.communities`. Base the description
on the community's `topFiles` and `graphify explain "<node>"` run on its
highest-degree member nodes (god nodes with that `community`, or symbols in its
`topFiles`), not on the community label (`explain` looks up a single node).

`confidence` covers `description` and `entryPoints`. `layer` is always an inference; the page labels it as inferred regardless of `confidence`.

### runLocally
```jsonc
{
  "prerequisites": [{ "name": "Node 20", "source": ".nvmrc", "confidence": "verified" }],
  "steps": [{ "title": "Install dependencies", "command": "npm ci",
              "notes": "optional plain-text note",
              "source": "README.md", "confidence": "verified" }],
  "unknowns": ["No .env.example; required environment variables are unclear."]
}
```
Steps are in run order. `command` is exactly what to type (or `""` for a
manual step). Steps taken from CI config but not from docs are `inferred`.

### whereThingsLive
```jsonc
[{ "task": "Add a new API endpoint", "look": ["src/routes/", "src/controllers/"],
   "community": 5, "source": "graph", "confidence": "inferred" }]
```
8-20 entries, phrased as tasks a new joiner would actually have
("Change the login page", "Add a DB migration"). `community` must be an id
in `graph.communities`, or `null`.

### flows
```jsonc
[{ "name": "Login request",
   "steps": [{ "node": "LoginController", "file": "src/auth/login.ts", "community": 0 }],
   "source": "graphify path", "confidence": "inferred" }]
```
3-5 flows. Every `node` must exist in graph.json. Build flows with
`graphify path "<A>" "<B>"` and `graphify query`.

### conventions
```jsonc
[{ "title": "Commit messages", "text": "Conventional Commits; use /writing-commit-messages.",
   "source": "team", "confidence": "verified" }]
```
Sources: CONTRIBUTING, lint/format configs, `.editorconfig`, CI checks, and the
team skills available in the session (e.g. the `team-skills` plugin).

### glossary
```jsonc
[{ "term": "Ledger", "definition": "Append-only record of money movements.",
   "source": "src/ledger/README.md", "confidence": "verified" }]
```
Domain terms and non-obvious module names only.

## Fields digest.py writes (read-only for you)

- `meta`: `repo`, `commit`, `generatedAt`, `scope`, `graphStale`, `graphStats{nodes,edges,communities}`
- `graph.communities[]`: `id`, `label`, `cohesion` (number or null), `size`, `topFiles[]`
- `graph.links[]`: `from`, `to`, `weight` (cross-community edge count)
- `graph.godNodes[]`: `id`, `label`, `file`, `community`, `degree`
