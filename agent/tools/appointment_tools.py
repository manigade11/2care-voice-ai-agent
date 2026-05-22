from memory.persistent_memory.patient_store import PatientMemoryStore


class AppointmentTools:
    def __init__(self, appointment_engine):
        self.appointment_engine = appointment_engine
        self.patient_store = PatientMemoryStore()

    def handle(self, intent: str, entities: dict, session_data: dict) -> dict:
        if intent == "check_availability":
            doctor_id = entities.get("doctor_id") or session_data.get("last_entities", {}).get("doctor_id")
            date = entities.get("date") or session_data.get("last_entities", {}).get("date")

            if not doctor_id or not date:
                return {
                    "success": False,
                    "message": "Please provide doctor_id and date to check availability.",
                }

            return self.appointment_engine.check_availability(doctor_id=doctor_id, date=date)

        if intent == "book_appointment":
            patient_id = entities.get("patient_id") or "patient_001"
            patient_profile = self.patient_store.get_patient_profile(patient_id) or {}

            doctor_id = (
                entities.get("doctor_id")
                or session_data.get("last_entities", {}).get("doctor_id")
                or patient_profile.get("preferred_doctor")
            )
            date = entities.get("date") or session_data.get("last_entities", {}).get("date")
            time = entities.get("time") or session_data.get("last_entities", {}).get("time")
            language = session_data.get("last_language", "en")

            missing_fields = []
            if not doctor_id:
                missing_fields.append("doctor_id")
            if not date:
                missing_fields.append("date")
            if not time:
                missing_fields.append("time")

            if missing_fields:
                return {
                    "success": False,
                    "message": f"Missing required fields for booking: {', '.join(missing_fields)}",
                }

            return self.appointment_engine.book_appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                date=date,
                time=time,
                language=language,
            )

        if intent == "cancel_appointment":
            appointment_id = entities.get("appointment_id")
            if not appointment_id:
                return {
                    "success": False,
                    "message": "Please provide appointment_id to cancel the appointment.",
                }

            return self.appointment_engine.cancel_appointment(appointment_id=appointment_id)

        if intent == "reschedule_appointment":
            appointment_id = entities.get("appointment_id")
            new_date = entities.get("date")
            new_time = entities.get("time")

            if not appointment_id or not new_date or not new_time:
                return {
                    "success": False,
                    "message": "Please provide appointment_id, new date, and new time to reschedule.",
                }

            return self.appointment_engine.reschedule_appointment(
                appointment_id=appointment_id,
                new_date=new_date,
                new_time=new_time,
            )

        return {
            "success": False,
            "message": "Sorry, I could not understand the request intent.",
        }