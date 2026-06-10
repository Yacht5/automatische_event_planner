import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.transip.email")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

NOTIFICATION_RECIPIENT = "events@yacht5.nl"


def _smtp_connection():
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context)
    server.login(SMTP_USER, SMTP_PASSWORD)
    return server


def send_quote_email(recipient_info, pdf_path):
    """Stuurt de offerte-PDF naar de klant via TransIP SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return {"status": "error", "message": "SMTP credentials missing in .env"}

    recipient_email = recipient_info.get("email")
    recipient_name  = recipient_info.get("name", "Gewaardeerde Klant")

    msg = EmailMessage()
    msg['Subject'] = "Uw persoonlijke offerte van Yacht 5"
    msg['From']    = f"Yacht 5 <{SMTP_USER}>"
    msg['To']      = recipient_email

    body = f"""Beste {recipient_name},

Bedankt voor uw interesse in het vieren van uw event bij Yacht 5!

Op basis van uw aanvraag hebben wij een eerste prijsindicatie voor u gegenereerd. U vindt deze in de bijlage van deze e-mail.

Wij nemen binnenkort persoonlijk contact met u op om de details te bespreken en een definitieve offerte op te stellen.

Met vriendelijke groet,

Het team van Yacht 5
"""
    msg.set_content(body)

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf',
                               filename=os.path.basename(pdf_path))

    try:
        with _smtp_connection() as server:
            server.send_message(msg)
        return {"status": "success", "message": f"Offerte verzonden naar {recipient_email}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


LANGUAGE_LABELS = {"NL": "Nederlands", "DE": "Duits", "EN": "Engels"}


def send_notification_email(event_data: dict, contact_info: dict, calculation: dict = None, moneybird_url: str = ""):
    """Stuurt een volledige notificatie naar yacht5@events.nl bij een nieuwe aanvraag."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return {"status": "error", "message": "SMTP credentials missing in .env"}

    c    = contact_info
    name = c.get('name', '—')
    date = event_data.get('date', '—')

    msg = EmailMessage()
    msg['Subject'] = f"Nieuwe aanvraag — {name} | {date}"
    msg['From']    = f"Yacht 5 Event Planner <{SMTP_USER}>"
    msg['To']      = NOTIFICATION_RECIPIENT

    catering         = event_data.get('catering', [])
    priced_items     = []
    on_request_items = []

    if calculation:
        for item in calculation.get('itemized', []):
            if item.get('on_request'):
                on_request_items.append(item['name'])
            else:
                unit_price = item.get('unit_price') or 0.0
                total      = item.get('total') or 0.0
                priced_items.append(
                    f"  {item['name']:<35} {item['quantity']} x €{unit_price:.2f} = €{total:.2f}"
                )
        on_request_items += calculation.get('on_request', [])
    else:
        priced_items = [f"  {i}" for i in catering]

    totals = calculation.get('totals', {}) if calculation else {}
    taal   = LANGUAGE_LABELS.get(c.get('language', 'NL'), c.get('language', '—'))
    land   = c.get('country', '—')
    adres  = ', '.join(p for p in [c.get('address',''), c.get('zipcode',''), c.get('city','')] if p) or '—'

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

    body_parts += priced_items if priced_items else ["  —"]

    if on_request_items:
        body_parts += ["", "  Op aanvraag: " + ", ".join(on_request_items)]

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
        "  Omschrijving:",
        f"  {event_data.get('description') or '—'}",
        "",
        "  Programma:",
        f"  {event_data.get('program') or '—'}",
        "",
        "  Vragen / opmerkingen:",
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

    try:
        with _smtp_connection() as server:
            server.send_message(msg)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        try:
            input_data = json.loads(sys.stdin.read())
            result = send_quote_email(input_data["contact"], input_data["pdf_path"])
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
