import json
import time
import re
import logging
from datetime import datetime
from openai import OpenAI
from backend.config import settings
from scheduler.appointment_engine import AppointmentEngine
from agent.prompt.system_prompt import VOICE_AGENT_SYSTEM_PROMPT

from backend.api.deps import appointment_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("LLMAgent") # Ee file ki peru peduthunnam


class LLMAgent:
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                print(f"Failed to initialize OpenAI client in LLMAgent: {e}")

    def run_turn(
        self,
        user_text: str,
        session_id: str,
        history: list,
        patient_profile: dict = None,
    ) -> tuple[str, str, dict, dict, float]:
        """
        Executes a conversation turn with the LLM.
        Returns:
            (reply_text, detected_intent, entities_saved, tool_result, latency_ms)
        """
        start_time = time.perf_counter()
        
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        current_day_str = datetime.now().strftime("%A")
        
        # Prepare system prompt context
        context_prompt = (
            f"{VOICE_AGENT_SYSTEM_PROMPT}\n\n"
            f"CURRENT CONTEXT:\n"
            f"- Today's Date: {current_date_str}\n"
            f"- Today's Day: {current_day_str}\n"
        )
        
        if patient_profile:
            context_prompt += (
                f"- Current Patient ID: {patient_profile.get('patient_id')}\n"
                f"- Current Patient Name: {patient_profile.get('name')}\n"
                f"- Patient Preferred Language: {patient_profile.get('preferred_language')}\n"
                f"- Patient Preferred Doctor: {patient_profile.get('preferred_doctor')}\n"
            )
        else:
            context_prompt += "- Current Patient ID: patient_001\n" # Default fallback
            
        messages = [{"role": "system", "content": context_prompt}]
        
        # Append sliding conversation history
        for turn in history[-8:]:
            messages.append({"role": turn["role"], "content": turn["text"]})
            
        messages.append({"role": "user", "content": user_text})

        # Define tools for OpenAI API
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check available timeslots for a doctor on a specific date.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "doctor_id": {
                                "type": "string",
                                "enum": ["dr_cardio_1", "dr_derma_1"],
                                "description": "Doctor ID to check availability for"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format (resolve relative dates first, e.g. tomorrow)"
                            }
                        },
                        "required": ["doctor_id", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "book_appointment",
                    "description": "Book a new clinical appointment for a patient.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "patient_id": {
                                "type": "string",
                                "description": "Patient ID (use patient_001 or profile patient_id)"
                            },
                            "doctor_id": {
                                "type": "string",
                                "enum": ["dr_cardio_1", "dr_derma_1"],
                                "description": "Doctor ID"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date in YYYY-MM-DD format"
                            },
                            "time": {
                                "type": "string",
                                "description": "Time in HH:MM 24-hour format"
                            },
                            "language": {
                                "type": "string",
                                "description": "Preferred language code (en, hi, ta)"
                            }
                        },
                        "required": ["patient_id", "doctor_id", "date", "time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_appointment",
                    "description": "Cancel an existing appointment.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "The unique UUID of the appointment to cancel"
                            }
                        },
                        "required": ["appointment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "reschedule_appointment",
                    "description": "Reschedule an existing appointment to a new date and time.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "string",
                                "description": "The unique UUID of the appointment"
                            },
                            "new_date": {
                                "type": "string",
                                "description": "New date in YYYY-MM-DD format"
                            },
                            "new_time": {
                                "type": "string",
                                "description": "New time in HH:MM format"
                            }
                        },
                        "required": ["appointment_id", "new_date", "new_time"]
                    }
                }
            }
        ]

        intent = "unknown"
        entities = {}
        tool_result = {}
        reply_text = ""

        try:
            if self.client and settings.openai_api_key:
                # Real OpenAI Conversation + Tool execution loop
                response = self.client.chat.completions.create(
                    model=settings.openai_chat_model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.2
                )
                
                response_message = response.choices[0].message
                
                # Check for tool calls
                if response_message.tool_calls:
                    messages.append(response_message)
                    
                    for tool_call in response_message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        intent = function_name
                        entities.update(function_args)
                        
                        # Execute matching tool
                        if function_name == "check_availability":
                            res = appointment_engine.check_availability(
                                doctor_id=function_args.get("doctor_id"),
                                date=function_args.get("date")
                            )
                        elif function_name == "book_appointment":
                            res = appointment_engine.book_appointment(
                                patient_id=function_args.get("patient_id") or (patient_profile.get("patient_id") if patient_profile else "patient_001"),
                                doctor_id=function_args.get("doctor_id"),
                                date=function_args.get("date"),
                                time=function_args.get("time"),
                                language=function_args.get("language") or (patient_profile.get("preferred_language") if patient_profile else "en")
                            )
                        elif function_name == "cancel_appointment":
                            res = appointment_engine.cancel_appointment(
                                appointment_id=function_args.get("appointment_id")
                            )
                        elif function_name == "reschedule_appointment":
                            res = appointment_engine.reschedule_appointment(
                                appointment_id=function_args.get("appointment_id"),
                                new_date=function_args.get("new_date"),
                                new_time=function_args.get("new_time")
                            )
                        else:
                            res = {"success": False, "message": "Unknown function"}

                        tool_result = res
                        
                        # Feed tool response back to LLM
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": json.dumps(res)
                        })
                    
                    # Call OpenAI again for the final verbal response
                    second_response = self.client.chat.completions.create(
                        model=settings.openai_chat_model,
                        messages=messages,
                        temperature=0.2
                    )
                    reply_text = second_response.choices[0].message.content
                else:
                    # Pure chat, no tool called
                    reply_text = response_message.content
                    # Simple heuristic mapping for intent logs
                    if "book" in user_text.lower():
                        intent = "book_appointment"
                    elif "cancel" in user_text.lower():
                        intent = "cancel_appointment"
                    elif "reschedule" in user_text.lower() or "move" in user_text.lower():
                        intent = "reschedule_appointment"
                    elif "avail" in user_text.lower() or "slot" in user_text.lower():
                        intent = "check_availability"
                    else:
                        intent = "chat"
            
            else:
                # ----------------------------------------------------
                # HIGH-FIDELITY FALLBACK AGENT (SMART LOCAL ENGINE)
                # ----------------------------------------------------
                lowered = user_text.lower()
                pid = patient_profile.get("patient_id") if patient_profile else "patient_001"
                pref_lang = patient_profile.get("preferred_language") if patient_profile else "en"
                
                # Check for script to determine language of output
                is_hindi = any(char in user_text for char in ["मुझे", "कल", "मिलना", "अपॉइंटमेंट", "समय", "डॉक्टर", "कार्डियो", "त्वचा"])
                is_tamil = any(char in user_text for char in ["நாளை", "மருத்துவர்", "நேரம்", "பதிவு", "வேண்டும்", "இருதய", "மாற்ற"])
                
                lang = "en"
                if is_hindi or pref_lang == "hi":
                    lang = "hi"
                elif is_tamil or pref_lang == "ta":
                    lang = "ta"
                
                # Dynamic specialty/doctor mapping
                doc = "dr_cardio_1"  # default
                if any(word in lowered for word in ["derma", "skin", "त्वचा", "சரும"]):
                    doc = "dr_derma_1"
                
                # Time extracts
                time_match = re.search(r"(\d{2}:\d{2})", user_text)
                time_val = time_match.group(1) if time_match else None
                if not time_val:
                    if "10:30" in lowered or "साढ़े दस" in lowered:
                        time_val = "10:30"
                    elif "11:00" in lowered or "11" in lowered:
                        time_val = "11:00"
                    elif "14:00" in lowered or "2" in lowered:
                        time_val = "14:00"
                    else:
                        time_val = "10:30" # Default logical slot
                
                # Date extracts
                date_match = re.search(r"(\d{4}-\d{2}-\d{2})", user_text)
                date_val = date_match.group(1) if date_match else None
                if not date_val:
                    if "tomorrow" in lowered or "कल" in lowered or "நாளை" in lowered:
                        # Tomorrow date
                        from datetime import timedelta
                        date_val = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                    else:
                        date_val = current_date_str # Today

                # ----------------------------------------------------
                # EXECUTE INTENT LOGIC (REORDERED FOR UX SAFETY)
                # ----------------------------------------------------
                if any(word in lowered for word in ["cancel", "remove", "हटाएं", "ரத்து"]):
                    intent = "cancel_appointment"
                    
                    # Fetch last booked appointment instead of asking for UUID
                    list_res = appointment_engine.list_appointments()
                    patient_appts = [a for a in list_res.get("appointments", []) if a["patient_id"] == pid and a["status"] == "booked"]
                    
                    if not patient_appts:
                        reply_text = "I couldn't find any active appointments to cancel." if lang == "en" else "मुझे रद्द करने के लिए कोई अपॉइंटमेंट नहीं मिला।"
                    else:
                        appt_id = patient_appts[-1]["appointment_id"]
                        entities = {"appointment_id": appt_id}
                        
                        tool_result = appointment_engine.cancel_appointment(appt_id)
                        if tool_result["success"]:
                            if lang == "hi":
                                reply_text = "आपका अपॉइंटमेंट सफलतापूर्वक रद्द कर दिया गया है।"
                            elif lang == "ta":
                                reply_text = "உங்கள் அப்பாயிண்ட்மெண்ட் வெற்றிகரமாக ரத்து செய்யப்பட்டது."
                            else:
                                reply_text = f"Your appointment on {patient_appts[-1]['date']} has been cancelled successfully."
                        else:
                            reply_text = "Could not cancel appointment."

                elif any(word in lowered for word in ["reschedule", "move", "change", "बदलें", "மாற்ற"]):
                    intent = "reschedule_appointment"
                    
                    # Fetch last booked appointment
                    list_res = appointment_engine.list_appointments()
                    patient_appts = [a for a in list_res.get("appointments", []) if a["patient_id"] == pid and a["status"] == "booked"]
                    
                    if not patient_appts:
                        reply_text = "You don't have any appointments to reschedule." if lang == "en" else "बदलने के लिए कोई अपॉइंटमेंट नहीं है।"
                    else:
                        appt_id = patient_appts[-1]["appointment_id"]
                        entities = {"appointment_id": appt_id, "new_date": date_val, "new_time": time_val}
                        
                        tool_result = appointment_engine.reschedule_appointment(appt_id, date_val, time_val)
                        if tool_result["success"]:
                            appt = tool_result["appointment"]
                            if lang == "hi":
                                reply_text = f"आपका अपॉइंटमेंट सफलतापूर्वक {appt['date']} को {appt['time']} बजे के लिए बदल दिया गया है।"
                            elif lang == "ta":
                                reply_text = f"உங்கள் முன்பதிவு {appt['date']} அன்று {appt['time']} மணிக்கு வெற்றிகரமாக மாற்றப்பட்டது."
                            else:
                                reply_text = f"Your appointment has been rescheduled to {appt['date']} at {appt['time']}."
                        else:
                            avail = appointment_engine.check_availability(doc, date_val)
                            slots = avail.get("available_slots", [])
                            reply_text = f"Sorry, that time is unavailable. Dr. {doc} is free at: {', '.join(slots)}"

                elif any(word in lowered for word in ["avail", "free", "slot", "खाली", "கிடைக்கும்"]):
                    intent = "check_availability"
                    entities = {"doctor_id": doc, "date": date_val}
                    tool_result = appointment_engine.check_availability(doc, date_val)
                    slots = tool_result.get("available_slots", [])
                    if lang == "hi":
                        reply_text = f"डॉ. के लिए {date_val} को उपलब्ध समय हैं: {', '.join(slots) if slots else 'कोई समय उपलब्ध नहीं है'}"
                    elif lang == "ta":
                        reply_text = f"மருத்துவர் செடியூல் {date_val} அன்று கிடைக்கும் நேரங்கள்: {', '.join(slots) if slots else 'நேரங்கள் எதுவும் இல்லை'}"
                    else:
                        reply_text = f"Doctor availability for {date_val}: {', '.join(slots) if slots else 'No free slots found'}."

                elif any(word in lowered for word in ["book", "schedule", "appointment", "मिलना", "பதிவு", "அப்பாயிண்ட்மெண்ட்"]):
                    intent = "book_appointment"
                    entities = {"patient_id": pid, "doctor_id": doc, "date": date_val, "time": time_val, "language": lang}
                    
                    # Perform check & book
                    tool_result = appointment_engine.book_appointment(
                        patient_id=pid, doctor_id=doc, date=date_val, time=time_val, language=lang
                    )
                    
                    if tool_result["success"]:
                        appt = tool_result["appointment"]
                        if lang == "hi":
                            reply_text = f"आपका अपॉइंटमेंट {appt['date']} को {appt['time']} बजे {appt['doctor_id']} के साथ सफलतापूर्वक बुक हो गया है।"
                        elif lang == "ta":
                            reply_text = f"உங்கள் முன்பதிவு {appt['date']} அன்று {appt['time']} மணிக்கு {appt['doctor_id']} மருத்துவரிடம் வெற்றிகரமாக முடிந்தது."
                        else:
                            reply_text = f"Appointment successfully booked for {appt['date']} at {appt['time']} with {appt['doctor_id']}."
                    else:
                        # Suggest alternatives on failure
                        avail = appointment_engine.check_availability(doc, date_val)
                        slots = avail.get("available_slots", [])
                        if lang == "hi":
                            reply_text = f"माफ़ कीजियेगा, वह समय उपलब्ध नहीं है। क्या आप उपलब्ध समय {', '.join(slots) if slots else 'कोई नहीं'} में से चुनना चाहेंगे?"
                        elif lang == "ta":
                            reply_text = f"மன்னிக்கவும், அந்த நேரம் கிடைக்கவில்லை. மாற்று நேரங்கள்: {', '.join(slots) if slots else 'இல்லை'}. இதில் ஏதேனும் ஒன்றை முன்பதிவு செய்யலாமா?"
                        else:
                            reply_text = f"Sorry, that slot is unavailable. Dr. {doc} is available at: {', '.join(slots) if slots else 'no slots'}. Would you like to pick one of these?"
                else:
                    # Friendly greetings & conversational responses
                    intent = "greeting"
                    if lang == "hi":
                        reply_text = "नमस्ते! मैं 2Care.ai वॉइस असिस्टेंट हूँ। मैं आपकी डॉक्टर अपॉइंटमेंट बुक करने या बदलने में मदद कर सकता हूँ। आप क्या करना चाहेंगे?"
                    elif lang == "ta":
                        reply_text = "வணக்கம்! நான் 2Care.ai குரல் உதவியாளர். உங்கள் அப்பாயிண்ட்மெண்ட் முன்பதிவு செய்ய நான் உங்களுக்கு உதவ முடியும். நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?"
                    else:
                        reply_text = "Hello! I am the 2Care.ai Assistant. I can help you check, book, reschedule, or cancel clinical appointments. How can I help you today?"

        except Exception as e:
            logger.error(f"Failed to process LLM turn: {e}", exc_info=True) # <-- Idi correct
            intent = "error"
            reply_text = "I'm having trouble processing that request. Could you repeat?"

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return reply_text, intent, entities, tool_result, round(elapsed_ms, 2)