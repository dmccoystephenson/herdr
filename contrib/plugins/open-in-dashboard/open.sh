#!/bin/sh
# Open the focused herdr pane in a local session dashboard.
#
# The URL is a template; {pane_id} is replaced with the pane's id. Set it, and
# optionally the opener, with environment variables or one KEY=value per line
# in "$HERDR_PLUGIN_CONFIG_DIR/config" (the file is read, never sourced):
#
#   HERDR_DASHBOARD_URL     default http://127.0.0.1:8787/3d?focus={pane_id}
#   HERDR_DASHBOARD_OPENER  default: wslview or explorer.exe on WSL, open on
#                           macOS, otherwise xdg-open
#
# The dashboard is probed first (when curl is installed): if nothing answers,
# no browser is opened and the action fails with a message instead.
set -u

DEFAULT_URL='http://127.0.0.1:8787/3d?focus={pane_id}'

die() {
    printf 'open-in-dashboard: %s\n' "$1" >&2
    exit 1
}

config_value() {
    file="${HERDR_PLUGIN_CONFIG_DIR:-}/config"
    [ -n "${HERDR_PLUGIN_CONFIG_DIR:-}" ] && [ -r "$file" ] || return 0
    sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$file" | tail -n 1 |
        sed 's/[[:space:]]*$//; s/^"\(.*\)"$/\1/; s/^'"'"'\(.*\)'"'"'$/\1/'
}

is_wsl() {
    [ -n "${WSL_DISTRO_NAME:-}" ] || [ -e /proc/sys/fs/binfmt_misc/WSLInterop ]
}

pane_id="${HERDR_PANE_ID:-${HERDR_ACTIVE_PANE_ID:-}}"
[ -n "$pane_id" ] || die "no pane id (run this as a herdr plugin action on a pane)"
case "$pane_id" in
    *[!A-Za-z0-9:._-]*) die "unexpected pane id: $pane_id" ;;
esac

template="${HERDR_DASHBOARD_URL:-$(config_value HERDR_DASHBOARD_URL)}"
[ -n "$template" ] || template="$DEFAULT_URL"
case "$template" in
    http://*|https://*) ;;
    *) die "HERDR_DASHBOARD_URL must start with http:// or https:// (got: $template)" ;;
esac
url=$(printf '%s\n' "$template" | sed "s/{pane_id}/$pane_id/g")

if command -v curl >/dev/null 2>&1; then
    curl -s -o /dev/null --max-time 2 "$url" ||
        die "nothing answered at $url; is the dashboard running? Nothing was opened."
fi

opener="${HERDR_DASHBOARD_OPENER:-$(config_value HERDR_DASHBOARD_OPENER)}"
if [ -z "$opener" ]; then
    if is_wsl && command -v wslview >/dev/null 2>&1; then
        opener=wslview
    elif is_wsl && command -v explorer.exe >/dev/null 2>&1; then
        opener=explorer.exe
    elif [ "$(uname -s)" = Darwin ]; then
        opener=open
    elif command -v xdg-open >/dev/null 2>&1; then
        opener=xdg-open
    else
        die "no opener found; set HERDR_DASHBOARD_OPENER. URL: $url"
    fi
fi

printf '%s\n' "$url"
case "$opener" in
    # explorer.exe exits 1 even when it opened the URL.
    explorer.exe|*/explorer.exe) "$opener" "$url" >/dev/null 2>&1; exit 0 ;;
    *) exec "$opener" "$url" ;;
esac
