import logging
import os
import requests as _requests
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

from api.models import QuotationRequest
from systems.quote_calculator import calculate_quote
from systems.moneybird import create_and_send_estimate


NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")

def _send_ntfy(title: str, message: str):
    print(f"[ntfy] topic='{NTFY_TOPIC}'")
    if not NTFY_TOPIC:
        print("[ntfy] NTFY_TOPIC niet ingesteld, overgeslagen")
        return
    try:
        resp = _requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": "high", "Tags": "bell"},
            timeout=5,
        )
        print(f"[ntfy] response: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"[ntfy] fout: {e}")

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/quotation")
async def create_quotation(request: QuotationRequest):
    try:
        event_data  = request.dict()
        calculation = calculate_quote(event_data)

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

        moneybird_result = create_and_send_estimate(
            calculation=calculation,
            event_data=event_data,
            contact_info=contact_info,
        )

        catering_str = ", ".join(event_data.get("catering", [])) or "—"
        _send_ntfy(
            title=f"Nieuwe aanvraag — {contact_info['name']}",
            message=(
                f"{event_data.get('date', '—')} | {event_data.get('timing', '—')} | "
                f"{event_data.get('guests', '—')} gasten\n"
                f"{event_data.get('location', '—')}\n"
                f"{catering_str}\n"
                f"{contact_info.get('email', '')} | {contact_info.get('phone', '')}"
            ),
        )


        return {
            "status":      "success",
            "calculation": calculation,
            "moneybird":   moneybird_result,
        }

    except Exception as e:
        logger.error("Fout bij verwerken aanvraag: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
