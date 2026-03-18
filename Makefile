# ============================================================
# Makefile – Code Quality Targets
# Quellcode liegt in: lib/
# Tools: vulture, skylos, pyright, mypy
# ============================================================

SRC_DIR := lib

.PHONY: lint lint-dead lint-types vulture skylos pyright mypy help

# ------------------------------------------------------------
# Hauptziel: alles auf einmal
# ------------------------------------------------------------
lint: lint-dead lint-types

# ------------------------------------------------------------
# Dead Code Detection
# ------------------------------------------------------------
lint-dead: vulture skylos

vulture:
	@echo ">>> vulture – Dead Code Detection..."
	vulture $(SRC_DIR) --min-confidence 80

skylos:
	@echo ">>> skylos – Dead Code Detection..."
	skylos $(SRC_DIR)

# ------------------------------------------------------------
# Type Checking
# ------------------------------------------------------------
lint-types: pyright mypy

pyright:
	@echo ">>> pyright – Type Checking..."
	-python -m pyright $(SRC_DIR)

mypy:
	@echo ">>> mypy – Type Checking..."
	-python -m mypy $(SRC_DIR) --ignore-missing-imports

# ------------------------------------------------------------
# Hilfe
# ------------------------------------------------------------
help:
	@echo ""
	@echo "Verfügbare Targets:"
	@echo "  make lint        – Alle Tools (dead code + types)"
	@echo "  make lint-dead   – Nur Dead Code (vulture + skylos)"
	@echo "  make lint-types  – Nur Type Checking (pyright + mypy)"
	@echo "  make vulture     – Nur vulture"
	@echo "  make skylos      – Nur skylos"
	@echo "  make pyright     – Nur pyright"
	@echo "  make mypy        – Nur mypy"
	@echo ""
