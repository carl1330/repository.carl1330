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

    @property
    def params(self) -> dict:
        params = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
            if isinstance(v, bool):
                v = str(v).lower()
            params[k] = v
        return params
