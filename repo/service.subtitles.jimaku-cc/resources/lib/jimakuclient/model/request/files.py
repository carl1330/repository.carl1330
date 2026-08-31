from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class JimakuFilesRequest:
    id: int
    episode: Optional[int] = None

    @property
    def params(self) -> Dict[str, Any]:
        params = {}
        if self.episode is not None:
            params["episode"] = self.episode
        return params
