import logging
from fastapi import APIRouter, HTTPException

from api.models import QuotationRequest
from systems.quote_calculator import calculate_quote
from systems.moneybird import create_and_send_estimate

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

        return {
            "status":      "success",
            "calculation": calculation,
            "moneybird":   moneybird_result,
        }

    except Exception as e:
        logger.error("Fout bij verwerken aanvraag: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
