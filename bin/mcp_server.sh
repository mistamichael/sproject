#!/usr/bin/env bash
# ================================================================
# SPROJECT - MCP-Server (KI-Schnittstelle, siehe doc/de/ki-schnittstelle.md)
# ================================================================
# Es läuft genau EIN moncapro-Server. Claude Code (.mcp.json) und die GUI
# (Menü Server -> Verbinden) verbinden sich beide mit ihm.
#
#   bin/mcp_server.sh                   HTTP auf http://127.0.0.1:8765/mcp (Standard)
#   bin/mcp_server.sh --port [N]        HTTP auf Port N (ohne N: 8765)
#   bin/mcp_server.sh --claude          stdio – nur für Skripte/Tests, die GUI kann sich nicht verbinden
#   bin/mcp_server.sh --help            diese Hilfe
# Weitere Argumente gehen an den Server, z. B. --project examples/tankdesign.json
# Im stdio-Modus darf nichts auf stdout erscheinen – daher setenv ohne Ausgabe.
# ================================================================

MODE=http
PORT=8765
EXTRA=()

usage() {
    echo "Aufruf: bin/mcp_server.sh [--port [N] | --claude] [--project DATEI]"
    echo
    echo "  (ohne)        HTTP auf http://127.0.0.1:8765/mcp – Claude Code und GUI verbinden sich damit"
    echo "  --port [N]    HTTP auf Port N (ohne N: 8765)"
    echo "  --claude      stdio – nur für Skripte/Tests, die GUI kann sich dann nicht verbinden"
    echo "  --project F   Projektdatei beim Start öffnen"
    echo "  --help        diese Hilfe"
    echo
    echo "Es läuft immer nur ein Server je Port; ein zweiter Start bricht mit einer Meldung ab."
}

while [ $# -gt 0 ]; do
    case "$1" in
        --claude) MODE=stdio; shift ;;
        --port)
            MODE=http; shift
            if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then PORT="$1"; shift; fi ;;
        -h|--help) usage; exit 0 ;;
        *) EXTRA+=("$1"); shift ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setenv.sh" > /dev/null

if [ ! -x "$PROJECT/.venv/bin/python" ]; then
    echo "ERROR: .venv nicht gefunden – zuerst bin/install_py.sh ausführen" >&2
    exit 1
fi

cd "$PROJECT" || exit 1
if [ "$MODE" = http ]; then
    exec "$PROJECT/.venv/bin/python" -m moncapro.mcp --http --port "$PORT" "${EXTRA[@]}"
fi
exec "$PROJECT/.venv/bin/python" -m moncapro.mcp "${EXTRA[@]}"
