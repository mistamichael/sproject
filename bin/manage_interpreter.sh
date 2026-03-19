#!/usr/bin/env bash
# Verwaltet die Python-Umgebung (activate/deactivate)
# Verwendung: source bin/manage_interpreter.sh activate
#             source bin/manage_interpreter.sh deactivate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PROJECT setzen falls noch nicht gesetzt
if [ -z "$PROJECT" ]; then
    export PROJECT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

case "$1" in
    activate)
        # Interpreter wählen
        if [ -n "$NETWORK_PYTHON" ]; then
            PYTHON_EXE="$NETWORK_PYTHON/python3"
        else
            PYTHON_EXE="python3"
        fi

        # venv erstellen falls nicht vorhanden
        if [ ! -d "$PROJECT/.venv" ]; then
            "$PYTHON_EXE" -m venv "$PROJECT/.venv"
        fi

        # venv aktivieren
        source "$PROJECT/.venv/bin/activate"
        export VIRTUAL_ENV_PYTHON="$PYTHON_EXE"
        ;;
    deactivate)
        deactivate 2>/dev/null || true
        unset VIRTUAL_ENV_PYTHON
        ;;
    *)
        echo "Usage: source manage_interpreter.sh [activate|deactivate]"
        return 1
        ;;
esac
