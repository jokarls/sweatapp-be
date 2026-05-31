# ADR 4: Testfilosofi och Efemära Miljöer

## Status
Accepted

## Kontext
För att säkerställa högsta möjliga tillförlitlighet och minimera "it works on my machine"-problem, behöver vi en strikt metodik för hur systemet verifieras. Vi vill undvika beroenden av statiska lokala miljöer (som en ständigt körande Docker Compose-databas) som kan hamna i ett inkonsistent tillstånd.

## Beslut
Vi inför följande principer för utveckling och verifiering av SweatCheck:

### 1. Självverifierande Backend
*   **Princip:** Systemets korrekthet bevisas uteslutande genom dess testsvit. Inga manuella steg eller "rök-tester" mot en manuellt startad miljö ska krävas för att verifiera en ändring.
*   **Implementering:** Varje ny funktion eller buggfix måste åtföljas av tester (Unit, Architecture eller Integration) som täcker de nya kraven.

### 2. Efemära Utvecklings- och Testmiljöer
*   **Princip:** Miljöer som krävs för verifiering (databas, cache, etc.) ska vara kortlivade (efemära) och hanteras helt av testverktygen.
*   **Implementering:** Vi använder **Testcontainers** för att snurra upp nödvändiga tjänster (PostgreSQL) vid behov. Testerna ansvarar för att starta, initiera (köra SQL-scheman), verifiera och stänga ner dessa resurser.
*   **Bortval av Docker Compose lokalt:** Vi använder inte Docker Compose för att "köra appen lokalt" i syfte att verifiera kodändringar. Testerna är den enda källan till sanning.

### 3. Deterministiska Integrationstester
*   Externa API-beroenden (Strava, OpenWeatherMap) ska alltid mockas i integrationstester för att säkerställa att testerna är snabba, stabila och kan köras utan nätverksåtkomst eller API-nycklar.

## Konsekvenser
*   **Enkel Onboarding:** En ny utvecklare behöver bara installera Poetry och köra `poetry run pytest`. Ingen manuell databaskonfiguration krävs.
*   **CI/CD-paritet:** Testerna körs på exakt samma sätt lokalt som i en CI-pipeline (t.ex. GitHub Actions), vilket eliminerar miljörelaterade buggar.
*   **Disciplin:** Kräver att vi investerar tid i att skriva robusta integrationstester tidigt, men sparar tid genom att eliminera manuell felsökning i trasiga lokala miljöer.
