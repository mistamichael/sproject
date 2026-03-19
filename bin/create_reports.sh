#!/usr/bin/env bash
# Erstellt Reports mit sproject.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$SCRIPT_DIR/manage_interpreter.sh" activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate Python environment"
    exit 1
fi

pushd "$PROJECT" > /dev/null
python -m lib.sproject "$@"
PYTHON_EXIT=$?
popd > /dev/null

source "$SCRIPT_DIR/manage_interpreter.sh" deactivate
exit $PYTHON_EXIT
