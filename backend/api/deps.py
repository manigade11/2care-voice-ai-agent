from scheduler.appointment_engine import AppointmentEngine
from memory.session_memory.redis_store import SessionMemoryStore
from memory.persistent_memory.patient_store import PatientMemoryStore
from scheduler.outbound_campaign_scheduler import OutboundCampaignScheduler

appointment_engine = AppointmentEngine()
session_memory_store = SessionMemoryStore()
patient_memory_store = PatientMemoryStore()
campaign_scheduler = OutboundCampaignScheduler()