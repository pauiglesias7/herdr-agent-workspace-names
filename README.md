# Agent Workspace Names

A [Herdr](https://herdr.dev) plugin that names each workspace after the session
title of the coding agent running inside it.

Claude Code gives every session a short title ("Fix login redirect",
"Migrate billing to Stripe"…). Herdr already sees it as the pane's terminal
title, but the workspace keeps the directory name, so five agents started from
the same repo all show up as `my-repo`. This plugin copies the agent's title to
the workspace, so the sidebar and the workspace picker (`prefix+w`) tell you
what each one is doing.

```
before                 after
──────                 ─────
my-repo                Fix login redirect
my-repo                Migrate billing to Stripe
my-repo                Flaky e2e test in checkout
```

## Install

```bash
herdr plugin install pauiglesias7/herdr-agent-workspace-names
```

Requires `python3` (standard library only). Tested with Claude Code; other
agents work too if they set a terminal title.

## Behaviour

- Runs when Herdr starts, when an agent changes state (e.g. finishes a turn)
  and when you switch workspace. Each run reconciles all workspaces.
- Only renames a workspace while it still has Herdr's default label (its
  directory name) or the title this plugin set last time. **Rename a workspace
  yourself (`prefix+shift+w`) and the plugin leaves it alone.** To hand it back,
  rename it to its directory name.
- If the agent's title changes later, the workspace follows.
- With several agents in one workspace, the first one with a title wins.
- Generic titles (`Claude Code`, the `claude …` command line before the
  session starts) are ignored.
- Titles longer than 40 characters are cut at a word boundary. Change it with
  `HERDR_WORKSPACE_NAMES_MAX_LEN`.

No hooks in your agent's config, no network access, no API calls: it only
reads Herdr's own state through the Herdr CLI.

## Uninstall

```bash
herdr plugin uninstall agent-workspace-names
```

Workspaces keep their current names.

## License

MIT
