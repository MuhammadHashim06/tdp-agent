# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any, Literal

# class IntentClassifyOut(BaseModel):
#     intent: str
#     confidence: float = Field(ge=0, le=1)
#     signals: List[str] = Field(default_factory=list)

# class DraftLLMOut(BaseModel):
#     draft: str
#     notes: Optional[str] = None

# class ReferralExtractOut(BaseModel):
#     # core requirements
#     patient_name: Optional[str] = None
#     dob: Optional[str] = None  # keep as string; normalize later (YYYY-MM-DD) if desired
#     diagnosis: Optional[str] = None
#     address: Optional[str] = None
#     insurance: Optional[str] = None
#     discipline_requested: Optional[str] = None

#     referral_source_name: Optional[str] = None
#     referral_source_org: Optional[str] = None
#     referral_source_email: Optional[str] = None
#     referral_source_phone: Optional[str] = None
#     referral_source_fax: Optional[str] = None

#     # additional useful fields
#     patient_id: Optional[str] = None
#     mrn: Optional[str] = None
#     ordering_provider: Optional[str] = None
#     requested_start_date: Optional[str] = None
#     visit_frequency: Optional[str] = None
#     authorization_required: Optional[str] = Field(default=None, description="yes|no|unknown")
#     language: Optional[str] = None
#     caregiver_contact: Optional[str] = None
#     special_instructions: Optional[str] = None

#     # traceability
#     extracted_from: Optional[str] = Field(default="email_body", description="email_body|attachments_names|mixed")
#     confidence_notes: Optional[str] = None

#     # if you want to keep raw snippets used for extraction
#     evidence: Optional[Dict[str, Any]] = None






from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class IntentClassifyOut(BaseModel):
    intent: str
    confidence: float = Field(ge=0, le=1)
    signals: List[str] = Field(default_factory=list)

class DraftLLMOut(BaseModel):
    draft: str
    notes: Optional[str] = None

class ReferralExtractOut(BaseModel):
    # core requirements
    patient_name: Optional[str] = None
    dob: Optional[str] = None  # keep as string; normalize later (YYYY-MM-DD) if desired
    diagnosis: Optional[str] = None
    address: Optional[str] = None
    insurance: Optional[str] = None
    discipline_requested: Optional[str] = None

    referral_source_name: Optional[str] = None
    referral_source_org: Optional[str] = None
    referral_source_email: Optional[str] = None
    referral_source_phone: Optional[str] = None
    referral_source_fax: Optional[str] = None

    # additional useful fields
    patient_id: Optional[str] = None
    mrn: Optional[str] = None
    ordering_provider: Optional[str] = None
    requested_start_date: Optional[str] = None
    visit_frequency: Optional[str] = None
    authorization_required: Optional[str] = Field(default=None, description="yes|no|unknown")
    language: Optional[str] = None
    caregiver_contact: Optional[str] = None
    special_instructions: Optional[str] = None

    # traceability
    extracted_from: Optional[str] = Field(default="email_body", description="email_body|attachments_names|mixed")
    confidence_notes: Optional[str] = None

    # if you want to keep raw snippets used for extraction
    evidence: Optional[Dict[str, Any]] = None





