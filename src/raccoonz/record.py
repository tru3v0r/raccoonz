from dataclasses import dataclass


@dataclass
class Record:
    params: dict
    url: str
    html: str | None
    data: dict
    timestamp: str
    lang: str
    bin_hash: str | None = None