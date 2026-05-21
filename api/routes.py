import logging
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

from api.models import QuotationRequest
from systems.quote_calculator import calculate_quote
from systems.moneybird import create_and_send_estimate
from systems.mail_sender import send_notification_email

router = APIRouter(prefix="/api")
logger = logging.getLogger(__name__)


@router.post("/quotation")
def create_quotation(request: QuotationRequest):
    contact_info = {
        "name":     request.contact.name,
        "email":    request.contact.email,
        "phone":    request.contact.phone,
        "company":  request.contact.company or "",
        "address":  request.contact.address or "",
        "zipcode":  request.contact.zipcode or "",
        "city":     request.contact.city or "",
        "country":  request.contact.country or "NL",
        "language": request.contact.language or "NL",
    }
    event_data = request.dict()

    try:
        calculation = calculate_quote(event_data)

        moneybird_result = create_and_send_estimate(
            calculation=calculation,
            event_data=event_data,
            contact_info=contact_info,
        )

        moneybird_url = moneybird_result.get("estimate_url", "")

        try:
            send_notification_email(
                event_data=event_data,
                contact_info=contact_info,
                calculation=calculation,
                moneybird_url=moneybird_url,
            )
        except Exception as mail_ex:
            logger.warning("Notificatie-mail mislukt: %s", mail_ex)

        return {
            "status":      "success",
            "calculation": calculation,
            "moneybird":   moneybird_result,
        }

    except Exception as e:
        logger.error("Fout bij verwerken aanvraag: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
