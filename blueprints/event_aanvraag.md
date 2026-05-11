# Blueprint: Event Aanvraag Workflow

## Doel
Verwerk een inkomende event-aanvraag van het formulier op de website tot een verzonden offerte-e-mail met PDF-bijlage.

## Benodigde input
Van het frontend-formulier (via `POST /api/quotation`):
- `category` — Zakelijk of Particulier
- `guests` — aantal gasten (integer)
- `date` — gewenste datum (YYYY-MM-DD)
- `location` — geselecteerde ruimte(s)
- `catering` — lijst met geselecteerde cateringopties
- `event_name`, `group_name` — namen voor het event (optioneel)
- `contact` — naam, e-mail, telefoon, bedrijf, adres
- `description`, `timing`, `program`, `questions` — aanvullende informatie (optioneel)

## Workflow

### Stap 1 — Bereken prijsindicatie
**System:** `systems/quote_calculator.py`

- Bepaal locatiekosten op basis van de geselecteerde ruimte
- Bereken cateringkosten per persoon × aantal gasten
- Bereken subtotaal, BTW (21%) en totaal
- Output: gestructureerd dict met `event_summary`, `itemized` en `totals`

### Stap 2 — Genereer PDF
**System:** `systems/pdf_generator.py`

- Maak een opgemaakte offerte-PDF op basis van de berekening
- Voeg contactgegevens en event-details toe
- Sla op als `offerte_{naam}.pdf`

### Stap 3 — Moneybird offerte (indien geconfigureerd)
**System:** `systems/moneybird.py`

Actief als `MONEYBIRD_API_TOKEN` aanwezig is in `.env`.

- Zoek contact op e-mailadres, anders nieuw contact aanmaken
- Maak een offerte aan met alle regelitems uit stap 1
- Op-aanvraag-items worden als informatieregel toegevoegd (€0,-)
- Verstuur de offerte via Moneybird naar het e-mailadres van de aanvrager
- Output: `estimate_id`, `reference`, directe URL naar de offerte in Moneybird

**Wisselen van account:** vervang alleen `MONEYBIRD_API_TOKEN` en `MONEYBIRD_ADMINISTRATION_ID` in `.env`.
Alle logica blijft hetzelfde.

### Stap 4 — PDF + e-mail (aanvullend)
**System:** `systems/pdf_generator.py` + `systems/mail_sender.py`

- Altijd actief, ook als Moneybird beschikbaar is
- Genereert een lokale PDF en verstuurt deze via SMTP

## Verwachte output
- Offerte aangemaakt en verzonden in Moneybird (als geconfigureerd)
- PDF-bestand op de server (tijdelijk)
- E-mail ontvangen door de aanvrager met prijsindicatie
- JSON-response naar de frontend met status, berekening en Moneybird-link

## Edge cases
- Ontbrekende Moneybird-credentials → Moneybird stap overgeslagen, rest gaat door
- Contact bestaat al in Moneybird → wordt hergebruikt op basis van e-mailadres
- Onbekende cateringoptie → overgeslagen in berekening
- Onbekende locatie → fallback naar standaardprijs
- BTW-tarief-ID niet gevonden → regelitem zonder BTW aangemaakt

## Moneybird configuratie
Vereiste waarden in `.env`:
- `MONEYBIRD_API_TOKEN` — Moneybird → Instellingen → API → Toegangstokens → Nieuw token
- `MONEYBIRD_ADMINISTRATION_ID` — het getal in de URL: `moneybird.com/{ID}/...`

## Bekend gedrag & beperkingen
- Prijzen zijn indicatief — geen bindende offerte
- BTW-tarief is vastgesteld op 21%
- Locatieprijzen staan hardcoded in `quote_calculator.py` — aanpassen daar bij tariefwijzigingen
- Gmail vereist een App Password (niet het account-wachtwoord) in `.env` als GMAIL_APP_PASSWORD
- Moneybird verstuurt de offerte-e-mail vanuit de naam/e-mail die is ingesteld in de Moneybird-administratie
