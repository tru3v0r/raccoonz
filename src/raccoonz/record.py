from dataclasses import dataclass

@dataclass
class Record:
    params: dict
    url: str | None
    html: str | None
    data: dict | None
    timestamp: str