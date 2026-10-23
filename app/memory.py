import time
from typing import Dict, List, Optional, Any

# 30 minutes expiration
SESSION_TTL_SECONDS = 1800.0

class ConversationMemory:
    """Session-isolated conversation memory with TTL expiration."""

    def __init__(self, ttl_seconds: float = SESSION_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired_keys = [
            sid for sid, data in self._sessions.items()
            if now - data["last_accessed"] > self.ttl_seconds
        ]
        for sid in expired_keys:
            del self._sessions[sid]

    def get_history(self, session_id: Optional[str]) -> List[Dict[str, str]]:
        """Retrieves history for the session. If session_id is None or expired, returns empty list."""
        if not session_id:
            return []

        self._cleanup_expired()
        session_data = self._sessions.get(session_id)
        if not session_data:
            return []

        now = time.time()
        if now - session_data["last_accessed"] > self.ttl_seconds:
            del self._sessions[session_id]
            return []

        session_data["last_accessed"] = now
        return list(session_data["messages"])

    def add_turn(self, session_id: Optional[str], user_input: str, assistant_output: str) -> None:
        """Records a completed turn in memory for session_id. No session_id means no memory stored."""
        if not session_id:
            return

        self._cleanup_expired()
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "created_at": now,
                "last_accessed": now,
                "messages": []
            }

        session_data = self._sessions[session_id]
        session_data["last_accessed"] = now
        session_data["messages"].append({"role": "user", "content": user_input})
        session_data["messages"].append({"role": "assistant", "content": assistant_output})

        # Cap memory length to prevent context flooding
        if len(session_data["messages"]) > 20:
            session_data["messages"] = session_data["messages"][-20:]

    def clear(self) -> None:
        self._sessions.clear()

memory_store = ConversationMemory()
