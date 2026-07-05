from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SearchSession:
    id: int
    title: str
    location: str
    query: str
    price_max: Optional[str] = None
    results: List[dict] = field(default_factory=list)


class SearchHistory:
    def __init__(self) -> None:
        self.sessions: Dict[int, SearchSession] = {}
        self.next_id = 1

    def add_session(self, location: str, query: str, price_max: Optional[str], results: List[dict]) -> SearchSession:
        session = SearchSession(
            id=self.next_id,
            title=f"{location} · {query}",
            location=location,
            query=query,
            price_max=price_max,
            results=results,
        )
        self.sessions[session.id] = session
        self.next_id += 1
        return session

    def get_session(self, session_id: int) -> Optional[SearchSession]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[SearchSession]:
        return list(self.sessions.values())

    def get_session_summary(self, session_id: int) -> Optional[str]:
        session = self.get_session(session_id)
        if not session:
            return None
        return f"{session.id}: {session.title} | {session.location} | {session.query}"
