from dataclasses import dataclass
from typing import Optional


@dataclass
class JimakuSearchRequest:
    anime: bool
    anilist_id: Optional[int] = None
    tmdb_id: Optional[str] = None
    query: Optional[str] = None
    after: Optional[int] = None
    before: Optional[int] = None
