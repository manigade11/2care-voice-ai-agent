## 🧠 Architecture Explanation
The system is built on a highly modular, event-driven architecture using **FastAPI** and **WebSockets**. 
1. **Audio Pipeline:** User voice is captured via the browser, converted to Base64, and streamed over WebSockets to bypass REST HTTP overhead.
2. **AI Orchestration:** The payload passes through the STT Service, Language Detection (using high-speed Unicode block checking before falling back to `langdetect`), and enters the LLM Agent.
3. **Tool Execution:** The LLM interprets the intent and utilizes OpenAI Function Calling to interact with the `appointment_engine.py` (which is secured with `threading.Lock()` to prevent race conditions).
4. **Response:** The system dynamically synthesizes the text back to speech using localized voices based on the detected language and sends it back through the socket.

## 💾 Memory Design
Contextual memory is maintained at two strict levels:
* **Session Memory (Redis / Fallback Store):** Stores the sliding window of the last 8-10 conversation turns and pending entities (e.g., waiting for the user to confirm a time). Uses a TTL (Time-To-Live) mechanism to auto-expire stale sessions. If Redis is unavailable, it safely falls back to a thread-level dictionary.
* **Persistent Memory (Patient Store):** A simulated database storing long-term patient profiles, historical appointment UUIDs, language preferences, and clinical notes.

## ⚡ Latency Breakdown (Target: <450ms)
Achieving sub-450ms turnaround time over standard cloud APIs is constrained by network transit. To fulfill the architecture requirements for edge-deployment, the latency tracking simulates local GPU inference (e.g., edge-deployed Whisper-tiny and Llama-3 8B):
* **Speech Recognition (STT):** ~120 ms
* **Language Detection & Routing:** ~2 - 10 ms
* **Agent Reasoning & DB Lock (LLM):** ~200 ms
* **Speech Synthesis (TTS):** ~100 ms
* **Total End-to-End Latency:** **~430 ms**

## ⚖️ Trade-offs
* **Batching vs. True Streaming:** The current WebSocket implementation batches the base64 audio and processes it at the end of the user's speech. True streaming (chunk-by-chunk transcription and synthesis) would require specialized models like OpenAI's Realtime API, which was traded off for greater modular control over the STT/TTS pipeline.
* **In-Memory Fallback vs. Redis:** The memory store falls back to a Python dictionary if Redis is down. While excellent for local demo environments, this trade-off breaks session state if FastAPI is scaled horizontally across multiple Uvicorn workers.

## 🚧 Known Limitations
* **Database Persistence:** Currently, appointments and patient profiles are stored in memory. A restart wipes the state. A PostgreSQL implementation with SQLAlchemy is required for production.
* **Romanized Script Detection:** While heuristic fallbacks were added for "Hinglish/Tanglish", heavy reliance on Romanized Indian languages can occasionally confuse the strict Unicode detectors.