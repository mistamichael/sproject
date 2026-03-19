#!/usr/bin/env bash
# Öffnet eine Shell mit gesetzten SPROJECT-Umgebungsvariablen
# Verwendung: source bin/get_cmd.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setenv.sh"

# Neue interaktive Shell starten (mit gesetzten Umgebungsvariablen)
exec "$SHELL"
