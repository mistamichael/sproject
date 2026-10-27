#!/usr/bin/env bash
# Startet den sproject MCP-Server (KI-Schnittstelle, siehe doc/de/ki-schnittstelle.md)
#   bin/mcp_server.sh                         stdio (für Claude Code / Claude Desktop)
#   bin/mcp_server.sh --http --port 8765      HTTP: http://127.0.0.1:8765/mcp
# Im stdio-Modus darf nichts auf stdout erscheinen – daher setenv ohne Ausgabe.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setenv.sh" > /dev/null

if [ ! -x "$PROJECT/.venv/bin/python" ]; then
    echo "ERROR: .venv nicht gefunden – zuerst bin/install_py.sh ausführen" >&2
    exit 1
fi

cd "$PROJECT" || exit 1
exec "$PROJECT/.venv/bin/python" -m mcp_server "$@"
