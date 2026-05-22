import json
from typing import Any, Dict, List

import redis
from backend.config import settings


class SessionMemoryStore:
    def __init__(self):
        self.ttl = settings.session_ttl_seconds
        self.client = None
        self.fallback_store = {}

        try:
            self.client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True
            )
            self.client.ping()
        except Exception:
            self.client = None

    def _key(self, session_id: str) -> str:
        return f"voice-agent:session:{session_id}"

    def _default_session(self, session_id: str) -> Dict[str, Any]:
        return {
            "session_id": session_id,
            "history": [],
            "last_language": "en",
            "last_intent": None,
            "last_entities": {},
        }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if self.client:
            try:
                raw = self.client.get(self._key(session_id))
                if raw:
                    return json.loads(raw)
            except Exception:
                pass

        return self.fallback_store.get(session_id, self._default_session(session_id))

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        if self.client:
            try:
                self.client.setex(
                    self._key(session_id),
                    self.ttl,
                    json.dumps(session_data),
                )
                return
            except Exception:
                pass

        self.fallback_store[session_id] = session_data

    def append_history(
        self,
        session_id: str,
        role: str,
        text: str,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        session_data = self.get_session(session_id)
        history: List[Dict[str, Any]] = session_data.get("history", [])

        history.append(
            {
                "role": role,
                "text": text,
                "metadata": metadata or {},
            }
        )

        session_data["history"] = history[-10:]
        self.save_session(session_id, session_data)
        return session_data

    def update_state(
        self,
        session_id: str,
        language: str | None = None,
        intent: str | None = None,
        entities: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        session_data = self.get_session(session_id)

        if language:
            session_data["last_language"] = language
        if intent:
            session_data["last_intent"] = intent
        if entities is not None:
            session_data["last_entities"] = entities

        self.save_session(session_id, session_data)
        return session_data

    def clear_session(self, session_id: str) -> None:
        if self.client:
            try:
                self.client.delete(self._key(session_id))
            except Exception:
                pass

        if session_id in self.fallback_store:
            del self.fallback_store[session_id]