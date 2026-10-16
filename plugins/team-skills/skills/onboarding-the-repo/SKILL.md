---
name: onboarding-the-repo
description: Use when the user explicitly asks for an onboarding guide, onboarding page or walkthrough of the whole repository, or says "onboard me" to this repo. Not for single questions about the code (where something lives, how to run it, how a part works) - answer those by querying the graph with graphify.
---

# Onboarding the Repo

Build an interactive onboarding page for the current repository: its
architecture (from a graphify knowledge graph), how to run it locally, where
things live, key flows, conventions and a glossary. Publish it as an Artifact.

Files beside this skill: `digest.py`, `template.html`, `schema.md`,
`examples/data-full.json`. `SKILL_DIR` below means this skill's folder: the
"Base directory for this skill" path shown when the skill loads.

**Running commands.**
- Use SKILL_DIR as that absolute base-directory path. Do not guess it from
  `~/.claude/skills/`; when installed from a plugin it lives in the plugin cache.
- `<PY>` is the path stored in `graphify-out/.graphify_python`. In PowerShell run `& (Get-Content graphify-out/.graphify_python) ...`. In bash run `"$(cat graphify-out/.graphify_python)" ...`. If that file is missing, use `python`.

## Honesty rules

- The architecture comes from the graph. Never describe structure the
  graph and files do not show.
- Every item gets `source` and `confidence`. If you are unsure, use `inferred`.
- Never invent a command, path, env var or node. Gaps go in `runLocally.unknowns`.

## Steps

### 0. Preflight
Run `git rev-parse --show-toplevel`. If it fails, or the output is not the
current directory, stop with: "Run this from the root of a git repository."
Compare the two paths after normalizing them (see **Normalizing paths**).

### 1. Make sure the graph exists and is fresh
**Normalizing paths.** Convert `\` to `/`, strip the trailing `/`, and compare
case-insensitively. A path is *inside* the repo only if the normalized path
equals the normalized repo root, or starts with the normalized repo root plus
`/` (`/repo2` is not inside `/repo`). graphify writes `.graphify_root` with
Windows backslashes, so always normalize it before comparing.

**Deriving SCOPE.** Always run the outside-repo check first. Read
`graphify-out/.graphify_root` (if missing, treat the scan root as the repo root)
and normalize it. If it is not inside the repo, it is *outside*, whatever else
was saved or chosen. Otherwise SCOPE is chosen in this order:
1. A subfolder the user chose during a build in THIS run is SCOPE (graphify
   writes `.graphify_root` before asking to narrow, so it can still point at the
   repo root).
2. After any full build or rebuild in this run, ignore data.json `meta.scope`;
   SCOPE is the `.graphify_root`-derived path.
3. Only on a re-run without a build, if `graphify-out/onboarding/data.json`
   exists, use its `meta.scope` (digest writes it in Step 2).
4. Otherwise SCOPE is the `.graphify_root`-derived repo-relative forward-slash
   path, or `.` if it equals the repo root.

SCOPE is never an absolute path.

Follow the first case that applies:

**1a. `graphify-out/graph.json` does not exist.** Invoke the `graphify` skill
on `.` and follow it fully. If it asks to narrow a large repo to a subfolder,
ask the user and use their answer as SCOPE. Then go to 1c.

**1b. `graphify-out/graph.json` exists.** Derive SCOPE.
- *Outside the repo:* the graph was built from another checkout or a moved
  repo and does not describe this repo. Tell the user and offer a full rebuild:
  invoke the `graphify` skill on `.` (not `--update`). If the user declines,
  **stop and report** that the existing graph does not describe this repo; do not digest or
  publish anything. If they accept, rebuild, then go to 1c.
- *Inside the repo:* run `<PY> SKILL_DIR/digest.py --check-stale .` (`<PY>` as
  under Running commands). Decide by the printed word, `stale` or `fresh`. Exit
  code 1 means stale, but the word decides. Any other output (for example a
  traceback) is an error: stop and report it. If it prints `stale`, ask: "The
  knowledge graph is older than the latest commit. Update it first
  (incremental, usually quick)?" If yes, invoke the graphify skill with
  `. --update`, then go to 1c. If no, set STALE=true. Continue to Step 2.

**1c. After any build, rebuild or update.** Derive SCOPE again (same order: outside check first, then a subfolder
chosen during the build, else `.graphify_root`; ignore data.json `meta.scope`). If the build failed, the graph is empty, or the scan root is
outside the repo, **stop and report it**. Never build the page from guesswork.
Do not run the stale check again; the graph is fresh. Continue to Step 2.

### 2. Digest the graph
```
<PY> SKILL_DIR/digest.py . graphify-out/onboarding/data.json --scope <SCOPE> [--stale]
```
Pass `--stale` only if STALE=true. Exit code 2 or 3 means there is no usable graph.
Stop and report it. The digest records SCOPE as `meta.scope` in that file.

### 3. Gather run information
Read whichever of these exist: `README*`, `CONTRIBUTING*`, `docs/` (getting
started), `package.json` / `pom.xml` / `build.gradle*` / `*.csproj` / `*.sln` /
`pyproject.toml` / `go.mod`, version files (`.nvmrc`, `.node-version`,
`global.json`, `.tool-versions`, `.python-version`), `docker-compose*.yml`,
`.env.example`, `Makefile`, `scripts/`, CI config (`.github/workflows/`,
`.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`), `.editorconfig`, and
lint/format configs. Also list the team skills available in this session (for
example `team-skills:writing-commit-messages`) for the Conventions section.

### 4. Author the content
Read `SKILL_DIR/schema.md` and `SKILL_DIR/examples/data-full.json`. Then fill
in every section of `graphify-out/onboarding/data.json` except `meta` and
`graph`:
- **architecture:** for each community, use its `topFiles` and
  `graphify explain "<node>"` run on the community's highest-degree member
  nodes (god nodes with that `community`, or symbols in its `topFiles`), never
  on the Claude-written label (`explain` looks up a single node). Write an entry for every community id. Assign `layer`.
- **runLocally:** use only what step 3 found.
- **whereThingsLive:** 8-20 tasks a new joiner would really have. Use
  `graphify query "<where is X handled>"` to place them.
- **flows:** 3-5 flows, built with `graphify path "<A>" "<B>"` between god
  nodes or entry points. Every node must exist in the graph.
- **conventions** and **glossary:** use what you found.

If `graphify` is not on PATH, use `<PY> -m graphify <subcommand> ...` or follow
the graphify skill's query/path/explain flow.

Write the file as UTF-8 JSON and check that it parses:
`<PY> -c "import json;json.load(open('graphify-out/onboarding/data.json',encoding='utf-8'))"`

### 5. Confirm before publishing
Tell the user in a few lines:
- the counts per section, how many items are `inferred`, and the unknowns
- Which artifact is affected. Check `graphify-out/onboarding-artifact.json`
  first. If it has a URL say "This will update <url> - anyone you've shared it
  with will see the changes." Otherwise say "This creates a new private
  artifact (only you can see it until you share the link)."
- Then ask: "Publishing puts this architecture description on claude.ai. Publish?"

**Wait for an explicit yes.** If the answer is no, stop. Then tell the user that the files are in
`graphify-out/onboarding/`.

### 6. Publish
1. Copy `SKILL_DIR/template.html` to `graphify-out/onboarding/index.html`, and
   replace `__REPO__` in it with `meta.repo` (HTML-escape it first: `&`, `<`,
   `>`, `"`). **Do not change the template's design or code.** It already meets
   the artifact page contract. Publish the template as is - skip artifact
   quickstart/design passes; do not redesign it.
2. If `graphify-out/onboarding-artifact.json` exists, read its `url` and
   read that artifact with the Artifact tool (`action: "read"`).
   - If the read works and you are a writer, publish
     `graphify-out/onboarding/index.html` with `url` set to it and
     `files: {"data.json": "graphify-out/onboarding/data.json"}`.
   - If the read fails, or you are not a writer, publish a new artifact as described below.
3. To publish a new artifact, publish `graphify-out/onboarding/index.html` with
   `files: {"data.json": "graphify-out/onboarding/data.json"}`, `icon: "map"`,
   and `description: "Interactive onboarding guide for <repo>."`
4. Write `{"url": "<artifact url>", "updatedAt": "<YYYY-MM-DD>"}` to
   `graphify-out/onboarding-artifact.json`.
5. Give the user the link. Mention that they can share it with teammates, and that
   re-running this skill updates the same link.
