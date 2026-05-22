from pydantic import BaseModel, Field
from backend.api.deps import appointment_engine, campaign_scheduler


class AvailabilityRequest(BaseModel):
    doctor_id: str = Field(..., min_length=1)
    date: str = Field(..., min_length=1)


class BookRequest(BaseModel):
    patient_id: str
    doctor_id: str
    date: str
    time: str
    language: str = "en"


class CancelRequest(BaseModel):
    appointment_id: str


class RescheduleRequest(BaseModel):
    appointment_id: str
    new_date: str
    new_time: str


class CampaignTriggerRequest(BaseModel):
    patient_id: str
    session_id: str = "campaign-session-001"


def trigger_campaign(payload: CampaignTriggerRequest):
    return campaign_scheduler.trigger_patient_reminder_campaign(
        patient_id=payload.patient_id,
        session_id=payload.session_id,
    )


def check_availability(payload: AvailabilityRequest):
    return appointment_engine.check_availability(
        doctor_id=payload.doctor_id,
        date=payload.date,
    )


def book_appointment(payload: BookRequest):
    return appointment_engine.book_appointment(
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        date=payload.date,
        time=payload.time,
        language=payload.language,
    )


def cancel_appointment(payload: CancelRequest):
    return appointment_engine.cancel_appointment(
        appointment_id=payload.appointment_id
    )


def reschedule_appointment(payload: RescheduleRequest):
    return appointment_engine.reschedule_appointment(
        appointment_id=payload.appointment_id,
        new_date=payload.new_date,
        new_time=payload.new_time,
    )


def get_appointment(appointment_id: str):
    return appointment_engine.get_appointment_by_id(appointment_id=appointment_id)


def list_appointments():
    return appointment_engine.list_appointments()