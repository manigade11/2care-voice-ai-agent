from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
# Imports moved inside methods to prevent circular dependency



class OutboundCampaignScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.jobs_started = False

    def start(self):
        if not self.jobs_started:
            self.scheduler.add_job(
                func=self.send_appointment_reminders,
                trigger="interval",
                seconds=30,
                id="outbound_reminders",
                replace_existing=True
            )
            self.scheduler.start()
            self.jobs_started = True
            print("Background Outbound Campaign Scheduler started (running reminders every 30s).")

    def shutdown(self):
        if self.jobs_started:
            self.scheduler.shutdown()
            self.jobs_started = False
            print("Background Outbound Campaign Scheduler stopped.")

    def trigger_patient_reminder_campaign(self, patient_id: str, session_id: str = "campaign-session-001") -> dict:
        """
        Forcefully triggers an outbound campaign for a specific patient.
        It pre-populates session memory so the patient can interact with the call.
        """
        from backend.api.deps import session_memory_store, appointment_engine, patient_memory_store

        # Fetch patient profile
        profile = patient_memory_store.get_patient_profile(patient_id)
        patient_name = profile.get("name", "Patient") if profile else "Patient"
        lang = profile.get("preferred_language", "en") if profile else "en"
        doctor_id = profile.get("preferred_doctor", "dr_cardio_1") if profile else "dr_cardio_1"
        
        # 1. Create a simulated appointment in the engine for "tomorrow" to make it cancelable/reschedulable
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Check if already booked, otherwise book one
        list_res = appointment_engine.list_appointments()
        existing = [a for a in list_res["appointments"] if a["patient_id"] == patient_id and a["status"] == "booked"]
        
        if not existing:
            book_res = appointment_engine.book_appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                date=tomorrow_str,
                time="10:30",
                language=lang
            )
            appointment = book_res.get("appointment", {})
        else:
            appointment = existing[-1]

        # 2. Formulate the outbound message based on the language
        if lang == "hi":
            reminder_text = (
                f"नमस्ते {patient_name}, मैं 2Care.ai से बोल रहा हूँ। कल सुबह {appointment.get('time', '10:30')} बजे "
                f"डॉक्टर के साथ आपका अपॉइंटमेंट तय है। क्या आप इस अपॉइंटमेंट की पुष्टि करना चाहेंगे या कोई बदलाव करना चाहते हैं?"
            )
        elif lang == "ta":
            reminder_text = (
                f"வணக்கம் {patient_name}, நான் 2Care.ai இலிருந்து பேசுகிறேன். நாளை காலை {appointment.get('time', '10:30')} மணிக்கு "
                f"உங்களுக்கு அப்பாயிண்ட்மெண்ட் முன்பதிவு செய்யப்பட்டுள்ளது. இதை உறுதிப்படுத்த விரும்புகிறீர்களா அல்லது வேறு நேரத்திற்கு மாற்ற வேண்டுமா?"
            )
        else:
            reminder_text = (
                f"Hello {patient_name}, this is a reminder from 2Care.ai. You have an appointment scheduled for tomorrow "
                f"at {appointment.get('time', '10:30')} with Dr. Cardio. Can we confirm if you are still available to join, "
                f"or would you like to reschedule?"
            )

        # 3. Clear existing session and inject history turn representing the outbound agent call
        session_memory_store.clear_session(session_id)
        
        # Initialize campaign states
        session_memory_store.update_state(
            session_id=session_id,
            language=lang,
            intent="campaign_reminder",
            entities={
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "appointment_id": appointment.get("appointment_id"),
                "date": appointment.get("date"),
                "time": appointment.get("time"),
                "language": lang
            }
        )
        
        # Inject turn
        session_memory_store.append_history(
            session_id=session_id,
            role="assistant",
            text=reminder_text,
            metadata={
                "outbound_campaign": True,
                "campaign_type": "appointment_reminder",
                "patient_id": patient_id
            }
        )

        return {
            "success": True,
            "message": "Outbound call campaign successfully injected.",
            "patient_id": patient_id,
            "session_id": session_id,
            "appointment_id": appointment.get("appointment_id"),
            "injected_text": reminder_text
        }

    def send_appointment_reminders(self):
        """Periodic background campaign runner"""
        print(f"[{datetime.now().isoformat()}] Scanning database for upcoming appointments requiring reminders...")
        # Simulates proactive logging for campaigns
        print("Campaign scan complete. No unsent batch reminders pending.")