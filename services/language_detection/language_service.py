import re
import time
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0


class LanguageDetectionService:
    def detect_language(self, text: str) -> str:
        """
        Detect language of text. Returns 'en', 'hi', or 'ta'.
        Utilizes high-speed Unicode block checking and Romanized heuristic checking 
        before falling back to langdetect.
        """
        if not text or not text.strip():
            return "en"

        # 1. Native Unicode block checking (Fastest)
        # Devanagari (Hindi): \u0900 - \u097F
        if re.search(r"[\u0900-\u097F]", text):
            return "hi"
            
        # Tamil: \u0B80 - \u0BFF
        if re.search(r"[\u0B80-\u0BFF]", text):
            return "ta"

        # 2. Hinglish / Tanglish Romanized checking (Fix for users typing in English script)
        lowered = text.lower()
        hinglish_words = ["mujhe", "kal", "appointment", "chahiye", "hai", "karo"]
        tanglish_words = ["naalai", "doctor", "paarkanum", "vendum", "appointment"]
        
        if sum(1 for w in hinglish_words if w in lowered) >= 2: 
            return "hi"
        if sum(1 for w in tanglish_words if w in lowered) >= 2: 
            return "ta"

        # 3. Fallback to langdetect for standard script
        try:
            detected = detect(text)
            if detected in ["hi", "ta", "en"]:
                return detected
            # Map common variations or defaults to English
            return "en"
        except Exception:
            return "en"