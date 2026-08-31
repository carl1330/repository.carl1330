from dataclasses import dataclass


@dataclass
class JimakuFileEntry:
    url: str
    name: str
    size: int
    last_modified: str
