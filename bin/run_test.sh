#!/usr/bin/env bash
# ============================================================================
# run_test.sh - Verarbeitet Projekt-Dateien mit sproject.py
#
# Usage:
#   ./bin/run_test.sh                           - Alle .json im examples Ordner
#   ./bin/run_test.sh <filename>                - Einzelne Projekt-Datei
#   ./bin/run_test.sh <filename> --export xlsx  - Excel-Report
#   ./bin/run_test.sh <filename> --export html  - HTML-Report
#   ./bin/run_test.sh <filename> --export zip   - Alle Grafiken als SVG-ZIP
#
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/setenv.sh"

if [ -f "$SCRIPT_DIR/_setenv.sh" ]; then
    echo "Lade lokale Umgebungseinstellungen aus _setenv.sh..."
    source "$SCRIPT_DIR/_setenv.sh"
fi

# ============================================================================
compare_results() {
    local project_file="$1"
    local basename
    basename="$(basename "$project_file" .json)"

    echo ""
    echo "--- Vergleiche Ergebnisse fuer $basename ---"
    echo ""

    mkdir -p "$PV_EXAMPLE_RESULTS"

    local differences_found=0
    local new_files=0

    for ext in json svg png; do
        for result_file in "$PV_RESULTS/${basename}"*."$ext"; do
            [ -f "$result_file" ] || continue
            local result_name
            result_name="$(basename "$result_file")"
            local reference_file="$PV_EXAMPLE_RESULTS/$result_name"

            if [ -f "$reference_file" ]; then
                if cmp -s "$result_file" "$reference_file"; then
                    echo "[OK]   $result_name stimmt mit Referenz ueberein"
                else
                    echo "[DIFF] $result_name unterscheidet sich von Referenz"
                    differences_found=1
                fi
            else
                echo "[NEU]  $result_name - erstelle Referenzdatei"
                cp "$result_file" "$reference_file"
                new_files=1
            fi
        done
    done

    [ $new_files -eq 1 ] && echo "" && echo "Neue Referenzdateien wurden in $PV_EXAMPLE_RESULTS erstellt."
    [ $differences_found -eq 1 ] && echo "" && echo "WARNUNG: Unterschiede zu Referenzdaten gefunden!" && \
        echo "Pruefe die Aenderungen und aktualisiere ggf. die Referenz manuell."
    echo ""
}

# ============================================================================
process_all_examples() {
    echo ""
    echo "============================================================================"
    echo "Verarbeite alle JSON-Dateien im examples Ordner"
    echo "Berechne CPM und erstelle alle Reports"
    echo "============================================================================"
    echo ""

    for f in "$PV_EXAMPLES"/*.json; do
        [ -f "$f" ] || continue
        echo ""
        echo "--- Verarbeite: $(basename "$f") ---"

        python "$PV_LIB/sproject.py" \
            --project "$f" \
            --output-dir "$PV_RESULTS" \
            --cfg-dir "$PV_CFG" \
            --export xlsx,md,json,txt,html,zip
        local result=$?

        [ $result -eq 0 ] && compare_results "$f"
        echo ""
    done

    echo ""
    echo "============================================================================"
    echo "Alle Dateien verarbeitet"
    echo "============================================================================"
    echo ""
}

# ============================================================================
usage() {
    echo "Usage: $(basename "$0") [filename] [OPTIONS]"
    echo ""
    echo "Argumente:"
    echo "  filename          Name der Projektdatei (mit oder ohne .json Erweiterung)"
    echo "                    Die Datei wird im examples Ordner gesucht."
    echo "                    Ohne Angabe werden alle .json Dateien verarbeitet."
    echo ""
    echo "Optionen:"
    echo "  --export FORMAT   Exportformate (kommagetrennt): txt, json, xlsx, md, html, zip"
    echo "                      txt  - Text-Report"
    echo "                      json - Netzplan als JSON"
    echo "                      xlsx - Excel-Report (Tabs per cfg/excel_export.cfg konfigurierbar)"
    echo "                      md   - Markdown-Report mit eingebetteten Mermaid-Diagrammen"
    echo "                      html - HTML-Report (Mermaid-Diagramme werden im Browser gerendert)"
    echo "                      zip  - Alle Grafiken als SVG-Dateien in einem ZIP-Archiv"
    echo "                             (Gantt, Netzplan, Ressourcen-Gantts via kroki.io)"
    echo ""
    echo "Hinweis:"
    echo "  CPM wird automatisch berechnet."
    echo "  Welche Tabs im Excel erscheinen, steuert cfg/excel_export.cfg (section_order)."
    echo ""
    echo "Beispiele:"
    echo "  $(basename "$0")                            Verarbeitet alle .json Dateien"
    echo "  $(basename "$0") tankdesign                 Verarbeitet tankdesign.json"
    echo "  $(basename "$0") tankdesign --export xlsx   Excel-Export"
    echo "  $(basename "$0") tankdesign --export html   HTML-Report"
    echo "  $(basename "$0") tankdesign --export zip    Alle Grafiken als SVG-ZIP"
    echo ""
    echo "Ergebnisse: $PV_RESULTS"
    echo "Referenzen: $PV_EXAMPLE_RESULTS"
    echo ""
}

# ============================================================================
# Hauptlogik
# ============================================================================

if [ $# -eq 0 ]; then
    process_all_examples
    exit 0
fi

PROJECT_FILE="$1"
shift

if [ ! -f "$PROJECT_FILE" ]; then
    PROJECT_FILE="$PV_EXAMPLES/$PROJECT_FILE"
fi

if [[ "$PROJECT_FILE" != *.json ]]; then
    PROJECT_FILE="${PROJECT_FILE}.json"
fi

if [ ! -f "$PROJECT_FILE" ]; then
    echo "Fehler: Projektdatei nicht gefunden: $PROJECT_FILE"
    echo ""
    usage
    exit 1
fi

echo ""
echo "============================================================================"
echo "Verarbeite Projektdatei: $PROJECT_FILE"
echo "============================================================================"
echo ""

python "$PV_LIB/sproject.py" --project "$PROJECT_FILE" --output-dir "$PV_RESULTS" --cfg-dir "$PV_CFG" "$@"
TEST_RESULT=$?

[ $TEST_RESULT -eq 0 ] && compare_results "$PROJECT_FILE"

echo ""
echo "============================================================================"
[ $TEST_RESULT -eq 0 ] && echo "Verarbeitung erfolgreich abgeschlossen" || echo "Verarbeitung fehlgeschlagen"
echo "============================================================================"
echo ""

exit $TEST_RESULT
