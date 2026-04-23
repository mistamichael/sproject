#!/usr/bin/env bash
# ================================================================
# SPROJECT - Umgebungsvariablen Setup
# ================================================================
# Dieses Skript muss gesourct werden: source bin/setenv.sh
# ================================================================

echo "Setting up environment variables for SPROJECT ..."

# Basis-Projektpfad (übergeordnetes Verzeichnis von bin/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Pfade für verschiedene Komponenten
export PV_BIN="$PROJECT/bin"
export PV_LIB="$PROJECT/lib"
export PV_DATA="$PROJECT/data"
export PV_CFG="$PROJECT/cfg"
export PV_THEMES="$PROJECT/cfg/themes"
export PV_LOG="$PROJECT/log"
export PV_TESTS="$PROJECT/tests"
export PV_RESULTS="$PROJECT/results"
export PV_EXAMPLES="$PROJECT/examples"
export PV_EXAMPLE_RESULTS="$PV_EXAMPLES/results"
export PV_WORK="$PROJECT/work"

# Python-Pfad erweitern (nur wenn noch nicht vorhanden)
if [[ ":$PYTHONPATH:" != *":$PV_LIB:"* ]]; then
    export PYTHONPATH="$PV_LIB:$PYTHONPATH"
fi

# Ordner erstellen falls sie nicht existieren
mkdir -p "$PV_BIN" "$PV_CFG" "$PV_LIB" "$PV_DATA" "$PV_LOG" "$PV_RESULTS" "$PV_EXAMPLES" "$PV_WORK"

echo ""
echo "================================================================"
echo "SPROJECT ENVIRONMENT SETUP COMPLETE"
echo "================================================================"
echo "PROJECT         = $PROJECT"
echo "PV_BIN          = $PV_BIN"
echo "PV_CFG          = $PV_CFG"
echo "PV_LIB          = $PV_LIB"
echo "PV_DATA         = $PV_DATA"
echo "PV_RESULTS      = $PV_RESULTS"
echo "PV_LOG          = $PV_LOG"
echo "PV_EXAMPLES     = $PV_EXAMPLES"
echo "PV_WORK         = $PV_WORK"
echo "PYTHONPATH      = $PYTHONPATH"
echo "================================================================"
echo ""
echo "Ready to use! Run: bin/create_reports.sh"
echo ""
