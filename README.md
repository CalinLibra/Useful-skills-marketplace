# Useful skills marketplace

Shared Claude Code skills for our dev team, distributed as a plugin marketplace.

## Plugins

| Plugin | Skills |
|---|---|
| `team-skills` | `/team-skills:writing-commit-messages` — Conventional Commit standard with a header checker<br>`/team-skills:onboarding-the-repo` — interactive onboarding page for a repo, built from a [graphify](https://github.com/safishamsi/graphify) knowledge graph |

## Install

In a terminal (or the same commands with a leading `/` inside a Claude Code session):

```bash
claude plugin marketplace add CalinLibra/Useful-skills-marketplace
claude plugin install team-skills@team-skills-marketplace
```

Then start a new session (or run `/reload-plugins`).

- **Private repo:** Claude Code uses your existing git credentials and never prompts. Make sure `git clone https://github.com/CalinLibra/Useful-skills-marketplace.git` works without a prompt first (for example `gh auth login` then `gh auth setup-git`).
- **Updates:** enable auto-update under `/plugin` → Marketplaces, or run `claude plugin update team-skills@team-skills-marketplace`. Plugins carry no `version`, so every commit to `main` is an update.
- **Old personal copies:** if you copied these skills into `~/.claude/skills/` before, delete them so you don't have two versions.

### Requirements

- `onboarding-the-repo` needs the `graphify` skill installed and Python 3.
- `writing-commit-messages` uses `bash` (Git Bash on Windows) for its header check.

### Auto-enable in a project

Commit this to a project's `.claude/settings.json`. Teammates who open the project and accept the trust prompt get the plugin automatically:

```json
{
  "extraKnownMarketplaces": {
    "team-skills-marketplace": {
      "source": { "source": "github", "repo": "CalinLibra/Useful-skills-marketplace" }
    }
  },
  "enabledPlugins": {
    "team-skills@team-skills-marketplace": true
  }
}
```

## Adding a skill

1. Create `plugins/team-skills/skills/<skill-name>/SKILL.md` (frontmatter `name` must equal the folder name).
2. Reference bundled files relative to the skill's base directory, never via `~/.claude/skills/`.
3. Validate: `claude plugin validate .` and `claude plugin validate ./plugins/team-skills`.
4. Commit using `/team-skills:writing-commit-messages`.

## Layout

```
.claude-plugin/marketplace.json
plugins/team-skills/
  .claude-plugin/plugin.json
  skills/
    writing-commit-messages/
    onboarding-the-repo/
```
