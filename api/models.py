from pydantic import BaseModel
from typing import List, Optional


class ContactInfo(BaseModel):
    name: str
    email: str
    phone: str
    company: Optional[str] = ""
    address: Optional[str] = ""
    zipcode: Optional[str] = ""
    city: Optional[str] = ""
    country: Optional[str] = "NL"


class QuotationRequest(BaseModel):
    category: str
    guests: int
    date: str
    location: str
    catering: List[str]
    event_name: Optional[str] = ""
    group_name: Optional[str] = ""
    contact: ContactInfo
    description: Optional[str] = ""
    timing: Optional[str] = ""
    program: Optional[str] = ""
    questions: Optional[str] = ""
