# CLAUDE.md – Projektanweisungen für Claude Code

## Projektstruktur

- Quellcode: `lib/`
- Sprache: Python

## Code-Qualität / Linting

Vor Code-Reviews, Refactorings oder nach größeren Änderungen immer den Lint-Lauf starten:

```bash
make lint
```

### Einzelne Tools

| Befehl            | Zweck                          |
|-------------------|-------------------------------|
| `make vulture`    | Dead Code (konservativ, 80%)  |
| `make skylos`     | Dead Code (ML-gestützt)       |
| `make pyright`    | Type Checking (schnell)       |
| `make mypy`       | Type Checking (streng)        |
| `make lint-dead`  | Nur Dead Code (beide Tools)   |
| `make lint-types` | Nur Type Checks (beide Tools) |

## Arbeitshinweise für Claude Code

- Vor dem Vorschlag von Refactorings: `make lint` ausführen und Ergebnisse berücksichtigen.
- Als toten Code markierte Symbole (vulture/skylos) nur entfernen, wenn der Nutzer dies explizit bestätigt.
- Typ-Fehler (pyright/mypy) bei neu generiertem Code direkt beheben, bevor der Code vorgeschlagen wird.
- `--ignore-missing-imports` bei mypy ist gesetzt – fehlende Stubs sind kein Blocker.
