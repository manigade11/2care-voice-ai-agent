import base64
import time
import logging
from openai import OpenAI
from backend.config import settings

# Setup Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("TTSService")


class TTSService:
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client in TTS: {e}", exc_info=True)

    def synthesize(self, text: str, language: str = "en") -> dict:
        """
        Synthesize text into speech (MP3) and return as base64 string.
        Returns:
            {
                "type": "audio" | "text_stub",
                "language": str,
                "text": str,
                "audio_base64": str (optional),
                "latency_ms": float
            }
        """
        start_time = time.perf_counter()
        
        if not text or not text.strip():
            elapsed = (time.perf_counter() - start_time) * 1000
            return {
                "type": "text_stub",
                "language": language,
                "text": "",
                "latency_ms": round(elapsed, 2)
            }

        # Map languages to professional voices
        # Whisper/TTS voices: 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'
        voice_map = {
            "en": "alloy",    # Clear American neutral accent
            "hi": "shimmer",  # Clear female Indian speaker profile
            "ta": "onyx"      # Deep male speaker profile
        }
        
        voice = voice_map.get(language, "alloy")

        try:
            if self.client and settings.openai_api_key:
                # Call OpenAI TTS
                response = self.client.audio.speech.create(
                    model=settings.openai_tts_model,
                    voice=voice,
                    input=text,
                    response_format="mp3"
                )
                
                # Get audio bytes
                audio_bytes = response.content
                audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
                
                elapsed = (time.perf_counter() - start_time) * 1000
                return {
                    "type": "audio",
                    "language": language,
                    "text": text,
                    "audio_base64": audio_base64,
                    "latency_ms": round(elapsed, 2)
                }
            else:
                # Fallback / Simulated mode:
                # Add a simulated synthesis delay (100ms standard)
                time.sleep(0.10)
                elapsed = (time.perf_counter() - start_time) * 1000
                return {
                    "type": "text_stub",
                    "language": language,
                    "text": text,
                    "audio_base64": "",
                    "latency_ms": round(elapsed, 2)
                }

        except Exception as e:
            logger.error(f"TTS Error: {e}", exc_info=True)
            elapsed = (time.perf_counter() - start_time) * 1000
            return {
                "type": "text_stub",
                "language": language,
                "text": text,
                "audio_base64": "",
                "latency_ms": round(elapsed, 2)
            }