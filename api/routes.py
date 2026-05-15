import logging
import os
import httpx
import requests as _requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

from api.models import QuotationRequest
from systems.quote_calculator import calculate_quote
from systems.moneybird import create_and_send_estimate


def _send_ntfy(title: str, message: str):
    topic = os.getenv("NTFY_TOPIC", "")
    if not topic:
        return
    try:
        httpx.post(
            f"https://ntfy.sh/{topic}",
            content=message.encode("utf-8"),
            headers={"Title": title, "Priority": "high", "Tags": "bell"},
            timeout=8,
        )
    except Exception:
        pass

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.get("/test-ntfy")
def test_ntfy():
    topic = os.getenv("NTFY_TOPIC", "")
    result = {"topic_in_env": topic or "(leeg)"}
    if topic:
        try:
            resp = _requests.post(
                f"https://ntfy.sh/{topic}",
                data="Test van Vercel".encode("utf-8"),
                headers={"Title": "Vercel test", "Priority": "high"},
                timeout=5,
            )
            result["ntfy_status"] = resp.status_code
            result["ntfy_response"] = resp.text[:200]
        except Exception as e:
            result["ntfy_error"] = str(e)
    return result


@router.post("/quotation")
def create_quotation(request: QuotationRequest):
    # Notificatie direct inline, exact zoals test-ntfy
    topic = os.getenv("NTFY_TOPIC", "")
    print(f"[quotation] NTFY_TOPIC={topic!r}")
    if topic:
        try:
            c = request.contact
            ed = request.dict()
            catering = ", ".join(ed.get("catering", [])) or "—"
            timing = ed.get("timing") or "Onbekend"
            msg = (
                f"Datum: {ed.get('date', '-')} | {timing}\n"
                f"Gasten: {ed.get('guests', '-')} | {ed.get('category', '-')}\n"
                f"Locatie: {ed.get('location', '-')}\n"
                f"Catering: {catering}\n"
                f"Omschrijving: {ed.get('description', '-')}\n"
                f"Programma: {ed.get('program') or '-'}\n"
                f"Vragen: {ed.get('questions') or '-'}\n"
                f"---\n"
                f"Naam: {c.name}\n"
                f"Email: {c.email}\n"
                f"Tel: {c.phone}\n"
                f"Bedrijf: {c.company or '-'}"
            )
            _requests.post(
                f"https://ntfy.sh/{topic}",
                data=msg.encode("utf-8"),
                headers={"Title": f"Aanvraag - {c.name}", "Priority": "high", "Tags": "bell"},
                timeout=8,
            )
        except Exception as ex:
            print(f"[quotation] ntfy fout: {ex}")

    contact_info = {
        "name":    request.contact.name,
        "email":   request.contact.email,
        "phone":   request.contact.phone,
        "company": request.contact.company or "",
        "address": request.contact.address or "",
        "zipcode": request.contact.zipcode or "",
        "city":    request.contact.city or "",
        "country": request.contact.country or "NL",
    }
    event_data = request.dict()

    try:
        calculation = calculate_quote(event_data)

        moneybird_result = create_and_send_estimate(
            calculation=calculation,
            event_data=event_data,
            contact_info=contact_info,
        )


        return {
            "status":      "success",
            "calculation": calculation,
            "moneybird":   moneybird_result,
        }

    except Exception as e:
        logger.error("Fout bij verwerken aanvraag: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
