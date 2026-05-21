import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_quote_email(recipient_info, pdf_path):
    """
    Sends the Beachclub WOW quotation PDF to the client via Gmail.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return {"status": "error", "message": "Gmail credentials missing in .env"}

    recipient_email = recipient_info.get("email")
    recipient_name = recipient_info.get("name", "Gewaardeerde Klant")

    msg = EmailMessage()
    msg['Subject'] = "Uw persoonlijke offerte van Beachclub WOW"
    msg['From'] = f"Beachclub WOW <{GMAIL_USER}>"
    msg['To'] = recipient_email
    
    body = f"""Beste {recipient_name},

Bedankt voor uw interesse in het vieren van uw event bij Beachclub WOW!

Op basis van uw aanvraag hebben wij een eerste prijsindicatie voor u gegenereerd. U vindt deze in de bijlage van deze email.

Wij nemen binnenkort persoonlijk contact met u op om de details te bespreken en een definitieve offerte op te stellen.

Met zonnige groet,

Het team van Beachclub WOW
Zwarte Pad 58, Scheveningen
"""
    msg.set_content(body)

    # Add PDF Attachment
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(pdf_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return {"status": "success", "message": f"Offerte verzonden naar {recipient_email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

LANGUAGE_LABELS = {"NL": "Nederlands", "DE": "Duits", "EN": "Engels"}

def send_notification_email(event_data: dict, contact_info: dict, calculation: dict = None, moneybird_url: str = ""):
    """Stuurt een volledige notificatie naar yacht5@events.nl bij een nieuwe aanvraag."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return {"status": "error", "message": "Gmail credentials missing in .env"}

    c = contact_info
    name = c.get('name', '—')
    date = event_data.get('date', '—')

    msg = EmailMessage()
    msg['Subject'] = f"Nieuwe aanvraag — {name} | {date}"
    msg['From'] = f"Yacht 5 Event Planner <{GMAIL_USER}>"
    msg['To'] = "yacht5@events.nl"

    catering = event_data.get('catering', [])

    # Splits catering in prijs-items en op-aanvraag items op basis van calculation
    priced_items = []
    on_request_items = []
    if calculation:
        for item in calculation.get('itemized', []):
            if item.get('on_request'):
                on_request_items.append(item['name'])
            else:
                priced_items.append(
                    f"  {item['name']:<35} {item['quantity']} x €{item['unit_price']:.2f} = €{item['total']:.2f}"
                )
        on_request_items += calculation.get('on_request', [])
    else:
        priced_items = [f"  {i}" for i in catering]

    totals = calculation.get('totals', {}) if calculation else {}

    taal = LANGUAGE_LABELS.get(c.get('language', 'NL'), c.get('language', '—'))
    land = c.get('country', '—')
    adres_parts = [c.get('address',''), c.get('zipcode',''), c.get('city','')]
    adres = ', '.join(p for p in adres_parts if p) or '—'

    body_parts = [
        "=" * 55,
        "  NIEUWE EVENT AANVRAAG — YACHT 5",
        "=" * 55,
        "",
        "── CONTACTGEGEVENS ──────────────────────────────────",
        f"  Naam:        {name}",
        f"  E-mail:      {c.get('email', '—')}",
        f"  Telefoon:    {c.get('phone', '—')}",
        f"  Bedrijf:     {c.get('company') or '—'}",
        f"  Adres:       {adres}",
        f"  Land:        {land}",
        f"  Taal:        {taal}",
        "",
        "── EVENTGEGEVENS ────────────────────────────────────",
        f"  Categorie:   {event_data.get('category', '—')}",
        f"  Datum:       {date}",
        f"  Tijden:      {event_data.get('timing') or '—'}",
        f"  Gasten:      {event_data.get('guests', '—')}",
        f"  Locatie:     {event_data.get('location', '—')}",
        f"  Eventnaam:   {event_data.get('event_name') or '—'}",
        f"  Groepsnaam:  {event_data.get('group_name') or '—'}",
        "",
        "── GESELECTEERDE OPTIES ─────────────────────────────",
    ]

    if priced_items:
        body_parts += priced_items
    else:
        body_parts.append("  —")

    if on_request_items:
        body_parts.append("")
        body_parts.append("  Op aanvraag: " + ", ".join(on_request_items))

    if totals:
        body_parts += [
            "",
            "── PRIJSINDICATIE ───────────────────────────────────",
            f"  Subtotaal:   €{totals.get('subtotal', 0):.2f}",
            f"  BTW (21%):   €{totals.get('vat_amount', 0):.2f}",
            f"  Totaal:      €{totals.get('total', 0):.2f}",
        ]

    body_parts += [
        "",
        "── AANVULLENDE INFORMATIE ───────────────────────────",
        f"  Omschrijving:",
        f"  {event_data.get('description') or '—'}",
        "",
        f"  Programma:",
        f"  {event_data.get('program') or '—'}",
        "",
        f"  Vragen / opmerkingen:",
        f"  {event_data.get('questions') or '—'}",
    ]

    if moneybird_url:
        body_parts += [
            "",
            "── MONEYBIRD ─────────────────────────────────────────",
            f"  {moneybird_url}",
        ]

    body_parts += ["", "=" * 55]

    msg.set_content("\n".join(body_parts))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # Test call
    import sys
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.stdin.read())
            result = send_quote_email(input_data["contact"], input_data["pdf_path"])
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
