---
name: writing-commit-messages
description: Use when writing or editing any git commit message, in any repository - git commit, amend, squash, reword, or drafting a commit message for the user or for a commit/PR command.
---

# Writing Commit Messages

Every commit message is a Conventional Commit with a short English header, in every repository.

## The message, in order

1. **Header** (one line): `<type>[(scope)][!]: <description>`
   - `type`: `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`
   - `scope` (optional): the area touched, lowercase - e.g. `spa`, `api`, `ingest`, `deps`
   - `!` before the colon only for a breaking change
   - `description`: **max 50 characters**, English, imperative mood ("add", not "added"/"adds"), a short summary of the change, no trailing period
2. **Body** (optional): blank line, then the details that matter (what changed, why), in English, wrapped at 72 columns.
3. **Trailers** (when required): blank line, then `BREAKING CHANGE: ...` and/or `Co-Authored-By: ...`.

## When `git log` shows another style

Use this format anyway. Long subjects, another language, or no type prefix in the history are the old style; this convention replaces it in every repository. Details the old style packed into the subject go in the body.

Merge commits that git generates itself (`Merge branch ...`, `Merge pull request ...`) keep git's default message.

## Check the header before committing

Count, don't estimate. In the Bash tool (Git Bash on Windows):

```bash
bash "<SKILL_DIR>/check-header.sh" "fix(spa): stop 403 on writes through Vite proxy"
```

`<SKILL_DIR>` is the "Base directory for this skill" path shown when this
skill loads (with forward slashes on Windows).

It prints `OK (37/50)` or what is wrong. Shorten and re-check until OK.

## Choosing the type

| Change | Type |
|---|---|
| New capability, page, endpoint | `feat` |
| Bug fix | `fix` |
| Docs/README only | `docs` |
| Formatting only, no logic | `style` |
| Restructure, same behavior | `refactor` |
| Faster, same behavior | `perf` |
| Tests only | `test` |
| Dependencies, build tooling, tsconfig | `build` |
| CI pipelines | `ci` |
| Other maintenance | `chore` |
| Reverting a commit | `revert` |

Mixed change: use the type of the main change; README updates that accompany a feature stay in that `feat`.

## Example

```
fix(spa): stop 403 on writes through Vite proxy

The short proxy form turned on changeOrigin, so Fastify's Origin
check rejected every POST/PUT/DELETE. Spell the proxy out in
vite.config.ts without changeOrigin.
```
