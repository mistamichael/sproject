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
export PV_DATA="$PROJECT/data"
export PV_CFG="$PROJECT/cfg"
export PV_THEMES="$PROJECT/cfg/themes"
export PV_LOG="$PROJECT/log"
export PV_TESTS="$PROJECT/tests"
export PV_RESULTS="$PROJECT/results"
export PV_WORK="$PROJECT/work"

# moncapro (Rechenkern) schreibt in dieselben Ordner. MONCAPRO_CFG bleibt ungesetzt:
# die Berechnungs-Konfiguration kommt aus dem Paket, PV_CFG enthält nur gui.cfg und Themes.
export MONCAPRO_DATA="$PV_DATA"
export MONCAPRO_LOG="$PV_LOG"
export MONCAPRO_RESULTS="$PV_RESULTS"
export MONCAPRO_WORK="$PV_WORK"


# Ordner erstellen falls sie nicht existieren
mkdir -p "$PV_BIN" "$PV_CFG" "$PV_DATA" "$PV_LOG" "$PV_RESULTS" "$PV_WORK"

echo ""
echo "================================================================"
echo "SPROJECT ENVIRONMENT SETUP COMPLETE"
echo "================================================================"
echo "PROJECT         = $PROJECT"
echo "PV_BIN          = $PV_BIN"
echo "PV_CFG          = $PV_CFG"
echo "PV_DATA         = $PV_DATA"
echo "PV_RESULTS      = $PV_RESULTS"
echo "PV_LOG          = $PV_LOG"
echo "PV_WORK         = $PV_WORK"
echo "================================================================"
echo ""
echo "Ready to use! Run: bin/create_reports.sh"
echo ""
