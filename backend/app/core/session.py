import asyncio
import json
import secrets
import time
from dataclasses import dataclass, field
from ..config import settings


@dataclass
class Session:
    id: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    created: float = field(default_factory=time.monotonic)
    events: list = field(default_factory=list)
    result: dict = field(default_factory=dict)
    cache: dict = field(default_factory=dict)
    changed: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None
    done: bool = False
    deleted: bool = False
    reserved: int = 0

    def emit(self, event, data):
        if self.deleted:
            return
        self.events.append({"id": str(len(self.events) + 1), "event": event, "data": json.dumps(data, ensure_ascii=False)})
        self.changed.set()


class SessionStore:
    def __init__(self):
        self.sessions: dict[str, Session] = {}

    def create(self, upload_size=0):
        self.purge()
        # Reserve worst-case text/result/event duplication plus input bytes.
        reservation = upload_size + settings.max_chars * 24 + 400_000
        if (
            len(self.sessions) >= settings.max_sessions
            or sum(s.reserved for s in self.sessions.values()) + reservation > settings.max_memory
        ):
            raise ValueError("The server is busy. Please try again after a few sessions expire.")
        session = Session(reserved=reservation)
        self.sessions[session.id] = session
        return session

    def get(self, sid):
        self.purge()
        return self.sessions.get(sid)

    def delete(self, sid):
        session = self.sessions.pop(sid, None)
        if session:
            session.deleted = True
            if session.task and not session.task.done():
                session.task.cancel()
            session.result.clear()
            session.events.clear()
            session.cache.clear()
            session.changed.set()

    def purge(self):
        for sid, session in list(self.sessions.items()):
            if time.monotonic() - session.created >= settings.ttl:
                self.delete(sid)


store = SessionStore()
