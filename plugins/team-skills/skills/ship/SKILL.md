---
name: ship
description: Use when the user asks to implement a feature, change or bug fix end to end with the team pipeline - "ship this", "/ship", "implement X with tests and commit it". Not for questions, explanations or one-line edits the user wants done directly.
---

# Ship

The team's lightweight pipeline: **plan with the user → code + tests per task →
one review → one fix round → final checks → commit**. It adapts to any project
through a small profile file. Keep the conversation short: one plan, one
approval, then run.

`SKILL_DIR` is this skill's folder: the "Base directory for this skill" path
shown when the skill loads.

## 1. Preflight

- Must be inside a git repository; otherwise stop and say so.
- Record `BASE` = `git rev-parse HEAD` and the current branch.
- Record `PRE_EXISTING` = the paths in `git status --porcelain`. The pipeline
  never commits these; if there are any, tell the user they will be left out.
- If the current branch is `main`, `master`, `develop` or the remote's default
  branch, create a new branch before any change: `feat/<short-slug>` (or
  `fix/<short-slug>` for a bug fix) and say so. If the user gave a task key
  (e.g. `DSH-12`), put it in the name: `feat/DSH-12-<short-slug>`; the commit
  skill reads the key from there.

## 2. Project profile

Read `.claude/pipeline.json` at the repo root. If it does not exist, build it:

```json
{
  "stack": "e.g. Node/TypeScript + React",
  "install": "npm ci",
  "test": "npm test",
  "lint": "npm run lint",
  "build": "npm run build",
  "conventions": "short notes from CLAUDE.md, CONTRIBUTING, .editorconfig, lint config"
}
```

- Take commands only from what exists: `package.json` scripts, `pom.xml` /
  `build.gradle*`, `*.csproj` / `*.sln`, `pyproject.toml` / `tox.ini`,
  `go.mod`, `Makefile`, CI config. Never invent a command.
- If no test command can be found, ask the user once. Lint and build may be
  omitted (leave the key out).
- Write the file and show it in two or three lines. Tell the user it can be
  committed and edited to fix the profile for the whole team.

## 3. Plan and approval

Read the code the request touches. Ask at most two questions, only if the
request is ambiguous in a way that changes the work. Then present:

- **Goal**: one sentence.
- **Tasks**: 1-6 tasks in build order, each with title, what changes, the
  files, and the tests to write. Each task must leave the tests passing.

If the whole change is tiny (one file, a few lines), say you will do it
directly: implement it yourself, run the profile's test command, then go to
step 5.

**Wait for an explicit yes.** Revise the plan if asked.

## 4. Run the pipeline

Run the Workflow tool with `name: "team-skills:implement-plan"` and
`args` as a JSON object (not a string):

```json
{ "goal": "...", "baseCommit": "<BASE>", "profile": { ...pipeline.json... },
  "tasks": [ { "title": "...", "details": "...", "files": ["..."], "tests": "..." } ] }
```

If that name is not found, use `scriptPath: "<SKILL_DIR>/../../workflows/implement-plan.js"`.

When it returns, check `status`:
- `completed` → step 5.
- `stopped`, `fix_failed` or `checks_failed` → **do not commit.** Report what
  failed (task, test output tail, findings) and ask the user how to proceed.
- If `reviewed` is false, say the review did not run and ask before committing.

## 5. Commit

1. Load the `team-skills:writing-commit-messages` skill (or
   `writing-commit-messages` if that is how it is installed) and follow it
   exactly: its message format, its message check and its commit command. The
   whole approved plan is one piece of work, so it is one commit.
2. Before committing, stage only the files this run changed: the paths in
   `git status --porcelain` that are not in `PRE_EXISTING`. Never use
   `git add -A` or `git add .`. Never stage secrets (`.env`, keys,
   credentials); if one shows up, stop and tell the user.
3. Commit as that skill says. **Do not push.**

## 6. Report

In a few lines: branch and commit hash, tasks done, review findings fixed,
minor findings left (one line each), final check results, and anything the
user should look at.
