# SweatCheck Backend

Backend for the SweatCheck app, built with FastAPI, asyncpg, and Clean Architecture.

## Filosofi
Detta projekt följer en **självverifierande** och **efemär** utvecklingsfilosofi (se [ADR 4](docs/adr/0004-test-philosophy.md)):
- **Sanningen finns i testerna:** Inga manuella verifieringssteg krävs.
- **Efemära miljöer:** Databaser och beroenden skapas och städas upp automatiskt av testsviten via Testcontainers.

## Utveckling

### Förutsättningar
- Python 3.11+
- [Poetry](https://python-poetry.org/)
- Docker (för att köra Testcontainers)

### Installation
```bash
poetry install
```

### Verifiering (Tester & Kvalitet)
Kör hela sviten för att bekräfta att allt fungerar:
```bash
# Kör alla tester (Unit, Architecture, Integration)
poetry run pytest

# Kontrollera linting och formatering
poetry run ruff check .

# Kontrollera statisk typning
poetry run mypy .
```

## Arkitektur
Projektet är strukturerat enligt Clean Architecture:
- `app/domain`: Ren affärslogik och interfaces.
- `app/infrastructure`: Teknisk implementering (DB, API-klienter).
- `app/api`: FastAPI routrar och DTOs.
