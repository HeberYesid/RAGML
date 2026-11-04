"""Bounded, owner-scoped in-memory sessions with expiration and atomic turns."""

import hashlib
import hmac
import secrets
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from ragml.conversation import SessionState


def utcnow() -> datetime:
    return datetime.now(UTC)


class SessionAccessError(ValueError):
    """The requested session is absent, expired, or belongs to someone else."""


class SessionBusyError(RuntimeError):
    """A bounded local service cannot accept another simultaneous turn."""


class OwnerTokens:
    """Authenticate opaque browser ownership; a restart invalidates all tokens."""

    def __init__(self) -> None:
        self._key = secrets.token_bytes(32)

    def encode(self, owner: UUID) -> str:
        signature = hmac.new(self._key, str(owner).encode(), hashlib.sha256).hexdigest()
        return f"{owner}.{signature}"

    def decode(self, token: str | None) -> UUID | None:
        if token is None or len(token) > 110:
            return None
        try:
            identity, _ = token.split(".", 1)
            owner = UUID(identity)
        except ValueError:
            return None
        return owner if hmac.compare_digest(self.encode(owner), token) else None


class InMemorySessionRepository:
    """One local process, no disk transcripts, bounded capacity and sliding TTL."""

    def __init__(
        self, ttl_seconds: int, capacity: int = 256, clock: Callable[[], datetime] | None = None
    ) -> None:
        self.ttl = timedelta(seconds=ttl_seconds)
        self.capacity = capacity
        self.clock = clock or utcnow
        self._records: dict[UUID, tuple[UUID, SessionState]] = {}
        self._lock = threading.RLock()
        self._turn_lock = threading.Lock()

    def _expire(self) -> None:
        now = self.clock()
        for key, (_, state) in tuple(self._records.items()):
            if now - state.last_seen_at >= self.ttl:
                del self._records[key]

    def load(self, session_id: UUID, store_id: str, owner_id: UUID) -> SessionState | None:
        with self._lock:
            self._expire()
            found = self._records.get(session_id)
            if found is None or found[0] != owner_id or found[1].store_id != store_id:
                return None
            return found[1].model_copy(deep=True)

    def save(self, state: SessionState, owner_id: UUID) -> None:
        with self._lock:
            self._expire()
            existing = self._records.get(state.session_id)
            if existing is not None and existing[0] != owner_id:
                raise SessionAccessError("session_not_found")
            if existing is None and len(self._records) >= self.capacity:
                raise SessionBusyError("session_capacity")
            self._records[state.session_id] = (owner_id, state.model_copy(deep=True))

    def delete(self, session_id: UUID, store_id: str, owner_id: UUID) -> None:
        with self._lock:
            if self.load(session_id, store_id, owner_id) is None:
                raise SessionAccessError("session_not_found")
            del self._records[session_id]

    @contextmanager
    def turn(
        self, session_id: UUID | None, store_id: str, owner_id: UUID, profile_revision: str
    ) -> Iterator[SessionState]:
        if not self._turn_lock.acquire(blocking=False):
            raise SessionBusyError("session_busy")
        try:
            state = self.load(session_id, store_id, owner_id) if session_id else None
            if session_id and (state is None or state.profile_revision != profile_revision):
                raise SessionAccessError("session_not_found")
            if state is None:
                now = self.clock()
                state = SessionState(
                    session_id=uuid4(),
                    store_id=store_id,
                    profile_revision=profile_revision,
                    created_at=now,
                    last_seen_at=now,
                )
            yield state
        finally:
            self._turn_lock.release()
