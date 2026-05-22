from uuid import uuid4
from datetime import datetime, timedelta
import threading


class AppointmentEngine:
    def __init__(self):
        # Initialize a lock for thread-safe operations to prevent race conditions
        self.lock = threading.Lock()
        
        # Dynamically generate today and tomorrow's dates in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        self.doctor_schedules = {
            "dr_cardio_1": {
                today: ["10:30", "14:00", "16:30"],
                tomorrow: ["09:00", "11:00", "15:00"],
            },
            "dr_derma_1": {
                today: ["10:00", "13:00", "17:00"],
                tomorrow: ["10:30", "12:30", "16:00"],
            },
        }

        self.appointments = {}

    def check_availability(self, doctor_id: str, date: str):
        available_slots = self.doctor_schedules.get(doctor_id, {}).get(date, [])
        booked_slots = [
            item["time"]
            for item in self.appointments.values()
            if item["doctor_id"] == doctor_id
            and item["date"] == date
            and item["status"] == "booked"
        ]
        free_slots = [slot for slot in available_slots if slot not in booked_slots]

        return {
            "success": True,
            "doctor_id": doctor_id,
            "date": date,
            "available_slots": free_slots,
        }

    def book_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        date: str,
        time: str,
        language: str = "en",
    ):
        with self.lock:
            if doctor_id not in self.doctor_schedules:
                return {
                    "success": False,
                    "message": "Invalid doctor ID",
                }

            try:
                appointment_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                if appointment_dt < datetime.now():
                    return {
                        "success": False,
                        "message": "Cannot book a past time slot",
                    }
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid date or time format. Use YYYY-MM-DD and HH:MM",
                }

            availability = self.check_availability(doctor_id, date)
            if time not in availability["available_slots"]:
                return {
                    "success": False,
                    "message": "Slot already booked or unavailable",
                    "alternative_slots": availability["available_slots"],
                }

            appointment_id = str(uuid4())
            self.appointments[appointment_id] = {
                "appointment_id": appointment_id,
                "patient_id": patient_id,
                "doctor_id": doctor_id,
                "date": date,
                "time": time,
                "status": "booked",
                "language": language,
            }

            return {
                "success": True,
                "message": "Appointment booked successfully",
                "appointment": self.appointments[appointment_id],
            }

    def cancel_appointment(self, appointment_id: str):
        with self.lock:
            appointment = self.appointments.get(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "message": "Appointment not found",
                }

            appointment["status"] = "cancelled"
            return {
                "success": True,
                "message": "Appointment cancelled successfully",
                "appointment": appointment,
            }

    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str):
        with self.lock:
            appointment = self.appointments.get(appointment_id)
            if not appointment:
                return {
                    "success": False,
                    "message": "Appointment not found",
                }

            availability = self.check_availability(appointment["doctor_id"], new_date)
            if new_time not in availability["available_slots"]:
                return {
                    "success": False,
                    "message": "Requested new slot is unavailable",
                    "alternative_slots": availability["available_slots"],
                }

            appointment["date"] = new_date
            appointment["time"] = new_time

            return {
                "success": True,
                "message": "Appointment rescheduled successfully",
                "appointment": appointment,
            }

    def get_appointment_by_id(self, appointment_id: str):
        appointment = self.appointments.get(appointment_id)
        if not appointment:
            return {
                "success": False,
                "message": "Appointment not found",
            }

        return {
            "success": True,
            "appointment": appointment,
        }

    def list_appointments(self):
        return {
            "success": True,
            "count": len(self.appointments),
            "appointments": list(self.appointments.values()),
        }