# ADR 3: Backend-arkitektur (Clean Architecture & DDD)

## Status
Accepted

## Kontext
För att säkerställa att SweatCheck är testbart, underhållbart och oberoende av yttre faktorer (som specifika ramverk eller API:er) krävs en strikt separation av ansvarsområden. Vi vill undvika "leaky abstractions" och säkerställa att affärslogiken är skyddad från tekniska detaljer.

## Beslut
Vi kommer att implementera backenden enligt principerna för **Clean Architecture** och **Domain-Driven Design (DDD)**.

### 1. Modulär Struktur
Applikationen delas upp i tre primära lager (moduler):

*   **`domain/` (Kärnan):** 
    *   Innehåller domänmodeller (Entities, Value Objects).
    *   Innehåller affärslogik (Domain Services) och beräkningsformler för svettförlust.
    *   Definierar **Interfaces** (Abstrakta Basklasser) för repositories och externa tjänster (t.ex. `IActivityRepository`, `IWeatherProvider`).
    *   **Beroende:** Inga yttre beroenden. Får inte importera från `api` eller `infrastructure`.

*   **`infrastructure/` (Implementering):**
    *   Innehåller konkreta implementeringar av domänens interfaces.
    *   Raw SQL-logik med `asyncpg` (Repository-mönstret).
    *   Klienter för externa API:er (Strava, OpenWeatherMap).
    *   **Beroende:** Beror på `domain`.

*   **`api/` (Presentation):**
    *   FastAPI-routers och Pydantic-schemas (DTOs).
    *   Översätter inkommande requests till domänanrop.
    *   **Beroende:** Beror på `domain` och injicerar implementeringar från `infrastructure`.

### 2. Katalogstruktur
```text
backend/
├── app/
│   ├── domain/         # Entities, Interfaces, Business Logic
│   ├── infrastructure/ # DB (asyncpg), API Clients, Framework Impl
│   ├── api/            # FastAPI, Routers, DTOs
│   └── main.py         # Composition Root (Dependency Injection)
├── tests/
│   ├── architecture/   # Tester för att validera lagergränser
│   ├── unit/           # Tester för enskilda moduler
│   └── integration/    # End-to-end med Testcontainers
```

### 3. Teststrategi
*   **Arkitekturtester:** Använda verktyg (t.ex. `pytest-archon` eller custom import-checks) för att säkerställa att `domain` förblir ren.
*   **Enhetstester:** Varje modul testas isolerat. Domänlogik testas utan databas.
*   **Integrationstester:** Körs mot en riktig PostgreSQL-instans via **Testcontainers**.
*   **Mocking:** Externa tjänster (Strava/Väder) mockas alltid i integrationstester för att säkerställa deterministiska resultat.

### 4. Dependency Injection
*   Vi använder en "Composition Root" (i `main.py` eller en dedikerad modul) för att injicera konkreta infrastruktur-klasser i API-routrarna, så att logiken förblir testbar.

### 5. Verktyg & Miljö
*   **Pakethantering:** Poetry (för beroenden, virtuella miljöer och paketering).
*   **Linting & Formatering:** Ruff (extremt snabb linter och formatterare som följer moderna Python-konventioner).
*   **Typkontroll:** Mypy (för statisk typsäkerhet i domänen och API:et).
*   **Task Runner:** Poetry (t.ex. `poetry run ruff check .`).

### 6. Felhantering (Error Handling Principles)
*   **Ingen tyst dämpning av fel:** Kritiska beräkningar, parsingar eller avkodningar (t.ex. vid validering av paginerings-cursors) får aldrig dämpas tyst (t.ex. genom try-catch som returnerar `None`). Fel ska propageras explicit.
*   **Tydlig feedback till klienten:** Felaktiga data eller korrupta requests ska resultera i explicita valideringsfel eller HTTP-undantag (t.ex. `400 Bad Request` med tydliga felmeddelanden), så att klienten kan agera på felet istället för att ignorera det.

## Konsekvenser
*   **Ökad komplexitet:** Fler filer och interfaces krävs initialt.
*   **Hög testbarhet:** Det blir extremt enkelt att byta ut t.ex. `asyncpg` mot en annan drivrutin eller mocka bort hela databasen för snabba tester.
*   **Tydlighet:** Affärsregler (hur svett beräknas) är centraliserade och dokumenterade i kod, inte gömda i SQL-frågor eller API-hanterare.
