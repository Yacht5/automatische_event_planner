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

def send_notification_email(event_data: dict, contact_info: dict, moneybird_url: str = ""):
    """Stuurt een notificatie naar events@yacht5.nl bij een nieuwe aanvraag."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return {"status": "error", "message": "Gmail credentials missing in .env"}

    msg = EmailMessage()
    msg['Subject'] = f"Nieuwe event aanvraag — {contact_info.get('name', '')} ({event_data.get('date', '')})"
    msg['From'] = f"Yacht 5 Event Planner <{GMAIL_USER}>"
    msg['To'] = "events@yacht5.nl"

    catering = event_data.get('catering', [])
    catering_str = ', '.join(catering) if catering else '—'

    body = f"""Nieuwe aanvraag binnengekomen via de event planner.

CONTACT
Naam:        {contact_info.get('name', '—')}
E-mail:      {contact_info.get('email', '—')}
Telefoon:    {contact_info.get('phone', '—')}
Bedrijf:     {contact_info.get('company', '—')}

EVENT
Datum:       {event_data.get('date', '—')}
Tijden:      {event_data.get('timing', '—')}
Gasten:      {event_data.get('guests', '—')}
Categorie:   {event_data.get('category', '—')}
Locatie:     {event_data.get('location', '—')}
Catering:    {catering_str}

Omschrijving:
{event_data.get('description', '—')}

Programma:
{event_data.get('program', '—')}

Vragen:
{event_data.get('questions', '—')}

{f'Moneybird offerte: {moneybird_url}' if moneybird_url else ''}
"""
    msg.set_content(body)

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
