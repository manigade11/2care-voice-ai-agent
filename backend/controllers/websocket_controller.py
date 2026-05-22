import json
import time
from fastapi import WebSocket, WebSocketDisconnect

from backend.api.deps import (
    appointment_engine,
    session_memory_store as session_store,
    patient_memory_store as patient_store
)
from services.speech_to_text.stt_service import SpeechToTextService
from services.text_to_speech.tts_service import TTSService
from services.language_detection.language_service import LanguageDetectionService
from agent.reasoning.llm_agent import LLMAgent

# Initialize services
stt_service = SpeechToTextService()
tts_service = TTSService()
language_service = LanguageDetectionService()
llm_agent = LLMAgent()


async def voice_agent_websocket(websocket: WebSocket):
    await websocket.accept()

    await websocket.send_json({
        "success": True,
        "message": "2Care.ai Voice Agent WebSocket Connected",
        "features": ["speech-to-text", "language-detection", "llm-reasoning-tools", "text-to-speech", "latency-breakdown"]
    })

    try:
        while True:
            raw_message = await websocket.receive_text()
            start_time = time.perf_counter()

            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "success": False,
                    "message": "Invalid JSON payload format",
                })
                continue

            session_id = payload.get("session_id", "demo-session-001")
            patient_id = payload.get("patient_id", "patient_001")
            user_text_input = payload.get("text", "").strip()
            
            # --- STAGE 1: SPEECH RECOGNITION (STT) ---
            stt_start = time.perf_counter()
            transcription, stt_latency = stt_service.transcribe(payload)
            
            # If both audio and text were absent
            if not transcription and not user_text_input:
                continue
            
            # Use transcribed text or fallback to text parameter
            user_query = transcription if transcription else user_text_input
            stt_latency = round((time.perf_counter() - stt_start) * 1000, 2) if payload.get("audio") else 0.0

            # --- STAGE 2: LANGUAGE DETECTION ---
            lang_start = time.perf_counter()
            detected_language = language_service.detect_language(user_query)
            lang_latency = round((time.perf_counter() - lang_start) * 1000, 2)

            # --- STAGE 3: PERSISTENT MEMORY CONTEXT ---
            patient_profile = patient_store.get_patient_profile(patient_id)
            if not patient_profile:
                # Dynamically register patient to keep persistent memory alive
                patient_profile = patient_store.update_patient_profile(patient_id, {
                    "patient_id": patient_id,
                    "name": "Walk-in Patient",
                    "preferred_language": detected_language
                })
            
            # Save user speech turn in session history
            session_store.append_history(
                session_id=session_id,
                role="user",
                text=user_query,
                metadata={
                    "language": detected_language,
                    "is_audio": bool(payload.get("audio"))
                }
            )

            # Retrieve conversation history
            session_data = session_store.get_session(session_id)
            history = session_data.get("history", [])

            # --- STAGE 4: LLM AGENT REASONING & TOOLS ---
            agent_start = time.perf_counter()
            reply_text, intent, entities, tool_result, _ = llm_agent.run_turn(
                user_text=user_query,
                session_id=session_id,
                history=history,
                patient_profile=patient_profile
            )
            agent_latency = round((time.perf_counter() - agent_start) * 1000, 2)

            # Update session entities and last active language
            merged_entities = dict(session_data.get("last_entities", {}))
            merged_entities.update(entities)
            if "language" not in merged_entities:
                merged_entities["language"] = detected_language

            session_store.update_state(
                session_id=session_id,
                language=detected_language,
                intent=intent,
                entities=merged_entities
            )

            # Save agent response in session history
            session_store.append_history(
                session_id=session_id,
                role="assistant",
                text=reply_text,
                metadata={
                    "language": detected_language,
                    "intent": intent,
                    "tool_result": tool_result
                }
            )

            # --- STAGE 5: TEXT-TO-SPEECH (TTS) ---
            tts_start = time.perf_counter()
            tts_res = tts_service.synthesize(reply_text, detected_language)
            audio_base64 = tts_res.get("audio_base64", "")
            tts_latency = round((time.perf_counter() - tts_start) * 1000, 2)

            # --- STAGE 6: METRICS & LATENCY TRACKING ---
            total_latency = round((time.perf_counter() - start_time) * 1000, 2)

            response_payload = {
                "success": tool_result.get("success", True) if tool_result else True,
                "session_id": session_id,
                "patient_id": patient_id,
                "transcription": user_query,
                "detected_language": detected_language,
                "intent": intent,
                "entities": merged_entities,
                "reply_text": reply_text,
                "audio": audio_base64,
                "latency_ms": total_latency,
                "latency_breakdown": {
                    "stt_ms": stt_latency,
                    "lang_detect_ms": lang_latency,
                    "agent_ms": agent_latency,
                    "tts_ms": tts_latency,
                    "total_ms": total_latency
                }
            }

            # Enrich response with tool-specific details
            if tool_result:
                if "appointment" in tool_result:
                    response_payload["appointment"] = tool_result["appointment"]
                if "available_slots" in tool_result:
                    response_payload["available_slots"] = tool_result["available_slots"]
                if "message" in tool_result:
                    response_payload["message"] = tool_result["message"]
                if "alternative_slots" in tool_result:
                    response_payload["alternative_slots"] = tool_result["alternative_slots"]

            # Log metrics in stdout for tracking
            print(
                f"[WS TURN] Lang: {detected_language} | Intent: {intent} | "
                f"STT: {stt_latency}ms | LangDet: {lang_latency}ms | "
                f"Agent: {agent_latency}ms | TTS: {tts_latency}ms | Total: {total_latency}ms"
            )

            await websocket.send_json(response_payload)

    except WebSocketDisconnect:
        print(f"[WS DISCONNECT] Session {session_id} disconnected.")
        return