#!/usr/bin/env bash
# Aktiviert die virtuelle Python-Umgebung
# Dieses Skript muss gesourct werden: source bin/activate_venv.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

source venv/bin/activate
echo "Virtuelle Umgebung aktiviert."
echo "Python-Version:"
python --version
echo ""
echo "Installierte Pakete:"
pip list
