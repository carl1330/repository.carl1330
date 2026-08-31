from dataclasses import dataclass
from typing import Optional


@dataclass
class Flag:
    adult: bool
    anime: bool
    external: bool
    movie: bool
    unverified: bool


@dataclass
class JimakuSearchResponse:
    id: int
    name: str
    last_modified: str
    flags: Flag
    anilist_id: Optional[int] = None
    creator_id: Optional[int] = None
    english_name: Optional[str] = None
    japanese_name: Optional[str] = None
    notes: Optional[str] = None
    tmdb_id: Optional[str] = None
