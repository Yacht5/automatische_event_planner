"""
Moneybird integration: maak een contact + offerte aan en stuur deze op.

Configuratie via .env:
    MONEYBIRD_API_TOKEN         — persoonlijk toegangstoken of OAuth token
    MONEYBIRD_ADMINISTRATION_ID — te vinden in de URL van je Moneybird-administratie

Om te switchen van testaccount naar klant: vervang alleen deze twee waarden.
"""

from __future__ import annotations

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN          = os.getenv("MONEYBIRD_API_TOKEN", "")
ADMINISTRATION_ID  = os.getenv("MONEYBIRD_ADMINISTRATION_ID", "")
BASE_URL           = f"https://moneybird.com/api/v2/{ADMINISTRATION_ID}"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type":  "application/json",
}


def _get(endpoint: str) -> dict | list:
    resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(endpoint: str, payload: dict) -> dict:
    resp = requests.post(f"{BASE_URL}/{endpoint}", json=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ── BELASTING-ID OPHALEN ──────────────────────────────────────────────────────

def get_tax_rate_id(percentage: str = "21") -> str | None:
    """Haal het Moneybird-ID op voor het BTW-tarief (standaard 21%)."""
    tax_rates = _get("tax_rates")
    for rate in tax_rates:
        if rate.get("percentage") == percentage and rate.get("tax_rate_type") == "sales_invoice":
            return rate["id"]
    # Fallback: eerste verkoop-tarief met dit percentage
    for rate in tax_rates:
        if rate.get("percentage") == percentage:
            return rate["id"]
    return None


# ── CONTACT ───────────────────────────────────────────────────────────────────

import logging as _logging
_log = _logging.getLogger(__name__)

def get_or_create_contact(contact: dict) -> str:
    """
    Zoek een bestaand contact op e-mail, anders aanmaken.
    Geeft het Moneybird contact-ID terug.

    contact = {
        "name":    "Jan Jansen",
        "email":   "jan@voorbeeld.nl",
        "phone":   "+31612345678",
        "company": "Voorbeeld BV",  # optioneel
    }
    """
    email = contact.get("email", "").strip()
    _log.info("get_or_create_contact — email=%s name=%s company=%s", email, contact.get("name"), contact.get("company"))

    # Zoek op e-mailadres en controleer exacte match
    results = _get(f"contacts?query={requests.utils.quote(email)}")
    _log.info("Zoekresultaten voor '%s': %d gevonden", email, len(results) if isinstance(results, list) else 0)
    if isinstance(results, list):
        for c in results:
            _log.info("  - contact email='%s' id=%s bedrijf='%s'", c.get("email"), c.get("id"), c.get("company_name"))
            if c.get("email", "").lower() == email.lower():
                _log.info("Bestaand contact gevonden: %s", c["id"])
                return c["id"]

    # Nieuw contact aanmaken
    parts    = contact.get("name", "").split(" ", 1)
    firstname = parts[0]
    lastname  = parts[1] if len(parts) > 1 else ""

    company = contact.get("company") or ""

    base_fields = {
        "phone":   contact.get("phone", ""),
        "address1": contact.get("address", ""),
        "zipcode":  contact.get("zipcode", ""),
        "city":     contact.get("city", ""),
        "country":  contact.get("country", "NL"),
    }

    if company:
        base_fields["company_name"] = company
    else:
        base_fields["firstname"] = firstname
        base_fields["lastname"]  = lastname

    # Probeer eerst met e-mail
    try:
        new_contact = _post("contacts", {"contact": {**base_fields, "email": email}})
    except Exception:
        # Fallback: aanmaken zonder e-mail, bewaar in attention veld
        base_fields["send_invoices_to_attention"] = f"E-mail: {email}"
        new_contact = _post("contacts", {"contact": base_fields})

    contact_id = new_contact["id"]

    # Bij bedrijfscontact: voeg contactpersoon toe via apart endpoint
    if company and (firstname or lastname):
        try:
            _post(f"contacts/{contact_id}/contact_people", {
                "contact_person": {"firstname": firstname, "lastname": lastname}
            })
        except Exception:
            pass

    return contact_id


# ── OFFERTE AANMAKEN ──────────────────────────────────────────────────────────

def create_estimate(contact_id: str, calculation: dict, event_data: dict, contact_info: dict = None) -> dict:
    """
    Maak een offerte aan in Moneybird op basis van de berekende quote.

    Geeft het aangemaakte offerte-object terug (inclusief estimate_id en reference).
    """
    tax_rate_id = get_tax_rate_id("21")

    details = []
    for item in calculation.get("itemized", []):
        line = {
            "description": item["name"],
            "price":       f"{item['unit_price']:.2f}",
            "amount":      str(item["quantity"]),
        }
        if tax_rate_id:
            line["tax_rate_id"] = tax_rate_id
        details.append(line)

    # Op-aanvraag-items als informatieregel toevoegen
    on_request = calculation.get("on_request", [])
    if on_request:
        details.append({
            "description": "Op aanvraag: " + ", ".join(on_request),
            "price":       "0.00",
            "amount":      "1",
        })

    event_summary = calculation.get("event_summary", {})
    reference = (
        f"Event {event_summary.get('date', '')} — "
        f"{event_summary.get('location', '')} — "
        f"{event_summary.get('guests', '')} gasten"
    )

    # Notitie met volledige eventdetails
    note_lines = [
        f"Type: {event_summary.get('type', '')}",
        f"Datum: {event_summary.get('date', '')}",
        f"Gasten: {event_summary.get('guests', '')}",
        f"Locatie: {event_summary.get('location', '')}",
    ]
    if event_data.get("timing"):
        note_lines.append(f"Tijdstip: {event_data['timing']}")
    if event_data.get("description"):
        note_lines.append(f"Omschrijving: {event_data['description']}")

    payload = {
        "estimate": {
            "contact_id":          contact_id,
            "reference":           reference,
            "estimate_date":       event_data.get("date", ""),
            "details_attributes":  details,
            "notes":               "\n".join(note_lines),
        }
    }

    # Bepaal workflow_id op basis van taal
    if contact_info:
        language = str(contact_info.get("language", "NL")).upper()
        if language == "EN":
            workflow_id = os.getenv("MONEYBIRD_WORKFLOW_ID_EN", "488287117251708393")
        elif language == "DE" or language == "DU":
            workflow_id = os.getenv("MONEYBIRD_WORKFLOW_ID_DE", "488285858919613949")
        else:
            workflow_id = os.getenv("MONEYBIRD_WORKFLOW_ID_NL", "488269925198071017")
        
        payload["estimate"]["workflow_id"] = workflow_id

    estimate = _post("estimates", payload)

    # Zet state naar open zodat de offerte verstuurd kan worden
    requests.patch(
        f"{BASE_URL}/estimates/{estimate['id']}",
        json={"estimate": {"state": "open"}},
        headers=HEADERS,
        timeout=15,
    )

    return estimate


# ── OFFERTE VERSTUREN ─────────────────────────────────────────────────────────

def send_estimate(estimate_id: str, email: str = "") -> dict:
    """Verstuur de offerte via Moneybird naar het e-mailadres van het contact.
    Bericht en onderwerp worden overgenomen uit de geselecteerde Moneybird workflow."""
    payload = {
        "estimate_email": {
            "delivery_method": "email",
            "email":           email,
        }
    }
    result = requests.patch(
        f"{BASE_URL}/estimates/{estimate_id}/send_estimate.json",
        json=payload,
        headers=HEADERS,
        timeout=15,
    )
    if not result.ok:
        raise Exception(f"Moneybird {result.status_code}: {result.text}")
    result.raise_for_status()
    return {
        "note": "Offerte verstuurd via Moneybird.",
        "url":  f"https://moneybird.com/{ADMINISTRATION_ID}/estimates/{estimate_id}",
    }


# ── HOOFD-FLOW ────────────────────────────────────────────────────────────────

def create_and_send_estimate(calculation: dict, event_data: dict, contact_info: dict) -> dict:
    """
    Volledige flow:
      1. Contact opzoeken of aanmaken
      2. Offerte aanmaken
      3. Offerte versturen

    Geeft een dict terug met estimate_id, reference en send_status.
    """
    contact_id = get_or_create_contact(contact_info)
    estimate   = create_estimate(contact_id, calculation, event_data, contact_info)
    estimate_id = estimate["id"]

    send_result = send_estimate(
        estimate_id,
        email=contact_info.get("email", ""),
    )

    return {
        "estimate_id":  estimate_id,
        "reference":    estimate.get("reference", ""),
        "estimate_url": f"https://moneybird.com/{ADMINISTRATION_ID}/estimates/{estimate_id}",
        "send_status":  send_result,
    }
