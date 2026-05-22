from typing import List, Optional
from pydantic import BaseModel


class AppointmentData(BaseModel):
    appointment_id: str
    patient_id: str
    doctor_id: str
    date: str
    time: str
    status: str
    language: str


class BaseAppointmentResponse(BaseModel):
    success: bool
    message: str


class AvailabilityResponse(BaseModel):
    success: bool
    doctor_id: str
    date: str
    available_slots: List[str]


class AppointmentResponse(BaseAppointmentResponse):
    appointment: Optional[AppointmentData] = None
    alternative_slots: Optional[List[str]] = None


class AppointmentListResponse(BaseAppointmentResponse):
    count: int
    appointments: List[AppointmentData]