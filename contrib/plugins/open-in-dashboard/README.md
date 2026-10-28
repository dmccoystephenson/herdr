# Open in dashboard

A small local plugin that opens the focused pane in a local session dashboard.
It runs the action against a URL template and fills in the pane's id
(`HERDR_PANE_ID`), so a dashboard that knows which agent session runs in which
pane can jump straight to it.

This plugin lives only in this fork and is not an official Herdr plugin.

## Install

```bash
herdr plugin link /path/to/herdr/contrib/plugins/open-in-dashboard
herdr plugin action invoke contrib.open-in-dashboard.open   # try it once
```

Bind it to a key in `~/.config/herdr/config.toml`:

```toml
[[keys.command]]
key = "prefix+shift+v"
type = "plugin_action"
command = "contrib.open-in-dashboard.open"
description = "open pane in dashboard"
```

## Configure

The default URL is `http://127.0.0.1:8787/3d?focus={pane_id}`. Change it, and
optionally the program that opens it, with environment variables visible to the
Herdr server, or with one `KEY=value` per line in the plugin's config file
(`$(herdr plugin config-dir contrib.open-in-dashboard)/config`). The file is
read, never sourced. Environment variables win.

| Setting | Default |
|---|---|
| `HERDR_DASHBOARD_URL` | `http://127.0.0.1:8787/3d?focus={pane_id}`. `{pane_id}` is replaced with the pane's id. It must be an `http://` or `https://` URL |
| `HERDR_DASHBOARD_OPENER` | `wslview` on WSL (then `explorer.exe`), `open` on macOS, otherwise `xdg-open` |

```text
HERDR_DASHBOARD_URL=http://127.0.0.1:9000/panes/{pane_id}
```

## When the dashboard is not running

When `curl` is installed, the URL is requested first with a two-second
timeout. If nothing answers, no browser is opened. The action fails with
`nothing answered at <url>; is the dashboard running?`, which `herdr plugin log
list --plugin contrib.open-in-dashboard` shows. Without `curl` the URL is opened
directly.

## Without the plugin

A one-line custom command keybinding does the same without the reachability
check. Custom commands receive `HERDR_ACTIVE_PANE_ID`:

```toml
[[keys.command]]
key = "prefix+shift+v"
type = "shell"
command = "xdg-open \"http://127.0.0.1:8787/3d?focus=$HERDR_ACTIVE_PANE_ID\""
description = "open pane in dashboard"
```

On WSL, use `wslview` in place of `xdg-open`.

The plugin's script also reads `HERDR_ACTIVE_PANE_ID` when `HERDR_PANE_ID` is
unset, so `command = "sh /path/to/open.sh"` with `type = "shell"` works too.

## Tests

`scripts/test_open_in_dashboard_plugin.py` runs the script with stub `curl`
and opener commands. It is part of `just maintenance-test`.
