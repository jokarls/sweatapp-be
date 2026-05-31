# ADR 1: Teknisk Arkitektur för SweatCheck

## Status
Accepted

## Kontext
Användaren vill bygga en mobilapplikation ("SweatCheck") för att spåra vätskeförlust under träning genom att kombinera automatisk aktivitetsdata från Strava med manuella invägningar. Systemet kräver hög precision i beräkningar, sömlös integration med externa API:er och en skalbar struktur för framtida prediktiv analys.

## Beslut
Vi kommer att implementera systemet med följande tekniska stack och principer:

### 1. Frontend
*   **Ramverk:** Flutter.
*   **Motivering:** Möjliggör en högpresterande upplevelse på både iOS och Android från en enda kodbas. Flutter är väl lämpat för datadrivna appar med anpassade gränssnitt.

### 2. Backend
*   **Språk:** Python.
*   **Ramverk:** FastAPI.
*   **Motivering:** Python har ett ekosystem av bibliotek för dataanalys som krävs för de framtida svettprofil-beräkningarna. FastAPI ger hög prestanda, automatisk OpenAPI-dokumentation och utmärkt stöd för asynkrona anrop (viktigt för API-integrationer).
*   **Paketering:** Docker. Applikationen ska köras i en container för att säkerställa portabilitet och enkel deployment.

### 3. API-kontrakt
*   **Metodik:** Design-first med OpenAPI.
*   **Verktyg:** `openapi-generator` för att generera Dart-klienter till Flutter.
*   **Motivering:** Säkerställer att frontend och backend alltid är synkroniserade och minskar risken för integrationsfel.

### 4. Databas
*   **Motor:** Managed PostgreSQL.
*   **Motivering:** En robust relationell databas är nödvändig för att hantera komplexa kopplingar mellan användare, aktiviteter, tokens och historisk svettdata. En managerad lösning minskar driftsbördan.

### 5. Integrationer
*   **Aktiviteter:** Strava API via OAuth2 och Webhooks.
*   **Väder:** OpenWeatherMap API för att hämta temperatur och luftfuktighet (historiskt och prognoser).
*   **Logik:** Backend hämtar automatiskt data vid Strava-webhooks för att minimera användarens manuella input.

## Konsekvenser
*   **Utvecklingsmiljö:** Ingen manuell uppsättning av databas krävs lokalt; verifiering sker via efemära miljöer i testerna (se ADR 4).
*   **API-synkronisering:** Varje ändring i API:et kräver en ny generering av Flutter-klienten.
*   **Kostnad:** Användning av managerad Postgres och API-anrop (Strava/Weather) kan medföra driftskostnader vid skalning.
*   **Säkerhet:** Tokens och personlig data (vikt) kräver noggrann hantering och kryptering i databasen.
