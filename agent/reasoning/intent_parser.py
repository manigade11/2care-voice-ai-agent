import re


class IntentParser:
    def parse_intent(self, text: str) -> dict:
        lowered = (text or "").strip().lower()

        intent = "unknown"

        if any(word in lowered for word in ["book", "schedule", "appointment"]):
            intent = "book_appointment"

        if any(word in lowered for word in ["cancel", "remove appointment"]):
            intent = "cancel_appointment"

        if any(word in lowered for word in ["reschedule", "change appointment", "move appointment"]):
            intent = "reschedule_appointment"

        if any(word in lowered for word in ["availability", "available", "slots", "free time"]):
            intent = "check_availability"

        entities = self.extract_entities(lowered)
        return {
            "intent": intent,
            "entities": entities,
        }

    def extract_entities(self, text: str) -> dict:
        entities = {}

        doctor_match = re.search(r"(dr_cardio_1|dr_derma_1)", text)
        if doctor_match:
            entities["doctor_id"] = doctor_match.group(1)

        patient_match = re.search(r"(patient_\d+)", text)
        if patient_match:
            entities["patient_id"] = patient_match.group(1)

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if date_match:
            entities["date"] = date_match.group(1)

        time_match = re.search(r"(\d{2}:\d{2})", text)
        if time_match:
            entities["time"] = time_match.group(1)

        appointment_match = re.search(
            r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            text
        )
        if appointment_match:
            entities["appointment_id"] = appointment_match.group(1)

        return entities