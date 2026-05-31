# ADR 2: Databaslager och Migreringar

## Status
Accepted

## Kontext
För att hantera databasändringar över tid och säkerställa att utvecklings-, test- och produktionsmiljöer är synkroniserade krävs ett robust system för databasmigreringar. Vi behöver också ett sätt att interagera med PostgreSQL från Python som är typ-säkert och effektivt.

## Beslut
Vi kommer att använda följande teknologier för databaslagret:

### 1. ORM: None (Raw SQL)
*   **Motivering:** Användaren föredrar att skriva SQL direkt för maximal kontroll och transparens. Vi kommer att använda ett bibliotek som `psycopg` eller `asyncpg` för att köra frågorna.

### 2. Migreringsramverk: Alembic (med raw SQL)
*   **Motivering:** Alembic kommer att användas för att hantera versionering och automatisering av databasuppdateringar, men istället för att autogenerera från SQLAlchemy-modeller kommer vi att skriva SQL-migreringar manuellt (eller använda `op.execute`). Detta ger den "automatiska" uppdateringsfunktionen vid deployment som önskas.

### 3. Namngivningskonvention
*   **Beslut:** Alla tabellnamn ska vara i **singular** (t.ex. `user`, `activity`).
*   **Motivering:** Följer användarens preferens och skapar en tydlig koppling mellan klassnamn i Python och tabellnamn i SQL.

### 4. Dataseparation (System vs Användare)
*   **Beslut:** För fält där data kan komma från både externa API:er och användarinput (t.ex. väder), ska vi lagra dessa i separata kolumner (t.ex. `temp_celsius_api` och `temp_celsius_user`).
*   **Motivering:** Gör det möjligt att analysera träffsäkerheten i API:erna och bevarar ursprunglig data även om användaren gör ändringar.

## Konsekvenser
*   **Workflow:** Utvecklare måste skapa en ny Alembic-migration varje gång en SQLAlchemy-modell ändras.
*   **Inlärning:** Kräver viss förståelse för Alembic-kommandon (`alembic revision --autogenerate`, `alembic upgrade head`).
