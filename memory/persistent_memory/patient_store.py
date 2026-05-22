from typing import Dict, Any


class PatientMemoryStore:
    def __init__(self):
        self.patient_profiles: Dict[str, Dict[str, Any]] = {
            "patient_001": {
                "patient_id": "patient_001",
                "name": "Amit Sharma",
                "preferred_language": "hi",
                "preferred_doctor": "dr_cardio_1",
                "preferred_hospital": "Apollo Delhi",
                "notes": "Patient prefers Hindi and has a history of high blood pressure."
            },
            "patient_002": {
                "patient_id": "patient_002",
                "name": "Karthik Subramanian",
                "preferred_language": "ta",
                "preferred_doctor": "dr_derma_1",
                "preferred_hospital": "Apollo Chennai",
                "notes": "Patient has sensitive skin, prefers Tamil conversation."
            },
            "patient_003": {
                "patient_id": "patient_003",
                "name": "Sarah Connor",
                "preferred_language": "en",
                "preferred_doctor": "dr_cardio_1",
                "preferred_hospital": "Apollo Bangalore",
                "notes": "Patient has scheduling preference for morning slots, talks English."
            }
        }

    def get_patient_profile(self, patient_id: str):
        return self.patient_profiles.get(patient_id)

    def save_patient_profile(self, patient_id: str, profile_data: dict):
        self.patient_profiles[patient_id] = profile_data
        return self.patient_profiles[patient_id]

    def update_patient_profile(self, patient_id: str, updates: dict):
        existing = self.patient_profiles.get(
            patient_id,
            {
                "patient_id": patient_id
            }
        )
        existing.update(updates)
        self.patient_profiles[patient_id] = existing
        return existing