# App-specifikation: SweatCheck (Arbetsnamn)

En mobilapp för löpare och atleter som vill optimera sin vätskestrategi genom att mäta och förutse vätskeförlust baserat på personlig svettprofil.

## 1. Syfte
Att ge användaren en exakt förståelse för hur mycket vätska de förlorar under olika förhållanden (temperatur, intensitet, klädsel) och använda denna data för att planera vätskeintag inför framtida pass och tävlingar.

## 2. Huvudfunktioner
*   **Loggning av vätskeförlust:** Beräkning baserad på viktföre/efter, intagen vätska och toalettbesök.
*   **Strava-integration:** Automatisk import av aktivitetsdata (sport, tid, medelpuls/intensitet, temperatur).
*   **Väder-berikning:** Automatisk hämtning av luftfuktighet och temperatur (som backup) via externa väder-API:er.
*   **Personlig Svettprofil:** En datadriven modell som lär sig hur användaren svettas i olika miljöer.
*   **Planeringsverktyg:** Förutse vätskebehov inför ett framtida pass baserat på planerad duration, intensitet och lokal väderprognos.
*   **Pushnotiser:** Påminnelse om att väga sig direkt när ett pass har registrerats på Strava.

## 3. Datamodell
### Manuell Input (Användaren)
*   **Vikt före passet:** (Default: senast kända vikt).
*   **Vikt efter passet:** Inmatas direkt efter avslutat pass.
*   **Vätska intagen:** Mängd vätska som druckits under passet (ml).
*   **Toalettbesök:** Enkel skala (Liten/Mellan/Stor) för att justera viktförlusten.
*   **Klädsel:** Skala (t.ex. 1-3) från "Minimalt" till "Lager-på-lager".

### Automatisk Data (API:er)
*   **Från Strava:** Sporttyp, varaktighet, medelpuls, maxpuls, Relative Effort (suffer score), temperatur (om tillgänglig).
*   **Från Väder-API:** Luftfuktighet, vind, exakt temperatur vid passets start/slut.

## 4. Användarflöde
1.  **Innan passet:** Användaren väger sig (frivilligt, annars används senast kända vikt).
2.  **Under passet:** Användaren loggar passet som vanligt med sin klocka/GPS (synkas till Strava).
3.  **Efter passet:**
    *   Strava skickar en webhook till appen.
    *   Appen skickar en pushnotis: "Bra kört! Dags att väga dig för att beräkna vätskeförlusten."
    *   Användaren öppnar appen, matar in vikt efter passet, hur mycket de druckit och klädsel.
    *   Appen presenterar resultatet: "Du förlorade 1.2 liter (0.8 liter/h)."
4.  **Planering:** Inför nästa pass kollar användaren appen för att se hur mycket de förväntas svettas och får en rekommenderad drickplan.

## 5. Framtida vision
*   **Tävlingsläge:** Specifika rekommendationer för lopp (t.ex. "Drick 150ml var 20:e minut").
*   **Trendanalys:** Se hur svetteffektiviteten förändras med kondition eller acklimatisering till värme.
