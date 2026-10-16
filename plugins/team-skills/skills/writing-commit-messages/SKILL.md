---
name: writing-commit-messages
description: Use when writing or editing any git commit message, in any repository - git commit, amend, squash, reword, a PR title, drafting a commit message for the user or for a commit/PR command, or deciding how to split work into commits.
---

# Writing Commit Messages

A commit message is a task, ready to file: a Romanian title and a short Romanian description. A dashboard reads tasks straight from commits without interpreting them, so this shape is a contract, the same in every repository.

## The message, in order

```
<type>[(scope)][!]: <titlu>

<descriere, 1-3 rânduri>

Item: DSH-12
```

1. **Header** (one line): `<type>[(scope)][!]: <titlu>`
   - `type`: `feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert` (the codes stay as they are)
   - `scope` (optional): the area touched, lowercase - e.g. `web`, `api`, `sync`, `deps`
   - `!` before the colon only for a breaking change
   - `titlu`: the task's title, **max 60 characters**, in Romanian with diacritics (`ș` `ț` with comma below), starting lowercase with a present-tense verb (`adaugă`, `repară`, `mută`, `scoate`), no trailing period. It names what works once this commit lands.
2. **Description** (required): a blank line, then 1-3 lines in Romanian, at most 72 characters each: what the change does and why. It becomes the task's description, so file names and implementation steps stay out.
3. **Trailers** (optional): a blank line, then one per line:
   - `Item: DSH-12` when the work has a key, from the branch name (`feat/DSH-12-...`) or from the user. Never invent a key; without one, leave the line out.
   - `BREAKING CHANGE: ...` for a breaking change.
   - `Co-Authored-By: ...` for a human co-author. For Claude, follow the repository's instructions.

## How many commits

One commit per finished piece of work, which is one task:

- The steps of one task (migration, endpoint, page, tests) go into **one** commit.
- A small fix found on the way (a typo, a stale comment) goes into that same commit.
- Two unrelated tasks are two commits, each with its own title. If they sit on one branch, the one that isn't the branch's task belongs on its own branch: propose that to the user before committing it there.
- Asked to commit unfinished work: still this format, the title naming what works so far; never `wip`, `fixup` or `misc`.
- A branch holds one task: its first commit proposes the task, later commits attach to it.
- A PR title uses the header format too: a squash merge makes it the commit on `main`.

## When `git log` shows another style

Use this format anyway: English subjects, long subjects or no type prefix are the old style. Merge commits that git generates itself (`Merge branch ...`, `Merge pull request ...`) keep git's default message.

## Check, then commit

Count, don't estimate. In the Bash tool (Git Bash on Windows), write the message to a file inside `.git`, check it, commit from it (`-F` keeps the diacritics and the blank lines):

```bash
msg="$(git rev-parse --git-dir)/MESAJ_COMMIT"
cat > "$msg" <<'EOF'
feat(web): adaugă filtrul pe parte la Pași următori

Lista de escaladare se filtrează după cine blochează (IT, Juridic,
DPO), ca fiecare blocaj să ajungă repede la cine trebuie să răspundă.

Item: DSH-12
EOF
bash "<SKILL_DIR>/check-message.sh" "$msg" && git commit -F "$msg"
```

`<SKILL_DIR>` is the "Base directory for this skill" path shown when this
skill loads (with forward slashes on Windows).

The check prints `OK (title 40/60, description 2/3 lines)` or what is wrong. Fix the file and re-check until OK.

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

Mixed change: the type of the main change. Docs and tests that come with a feature stay in that `feat`.
