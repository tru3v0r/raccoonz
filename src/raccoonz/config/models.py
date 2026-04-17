from dataclasses import dataclass, field
from typing import Any

from ..constants import bin_keys
from ..constants import config


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str
    fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]):
        return cls(
            name=name,
            path=data.get(bin_keys.ENDPOINT_PATH),
            fields=data.get(bin_keys.FIELDS, {}),
        )


@dataclass(frozen=True)
class Bin:
    name: str
    hash: str
    raw: dict[str, Any]
    url: str | None
    fetcher: str
    parser: str
    fetch: dict[str, Any]
    filters: dict[str, Any]
    endpoints: dict[str, Endpoint]

    @classmethod
    def from_dict(cls, raw: dict[str, Any], hash_value: str):
        endpoints_raw = raw.get(bin_keys.ENDPOINTS, {})
        endpoints = {
            endpoint_name: Endpoint.from_dict(endpoint_name, endpoint_data)
            for endpoint_name, endpoint_data in endpoints_raw.items()
        }

        return cls(
            name=raw.get(bin_keys.NAME, ""),
            hash=hash_value,
            raw=raw,
            url=raw.get(bin_keys.URL),
            fetcher=raw.get(bin_keys.FETCHER, config.DEFAULT_FETCHER),
            parser=raw.get(bin_keys.PARSER, config.DEFAULT_PARSER),
            fetch=raw.get(bin_keys.FETCH, {}),
            filters=raw.get(bin_keys.FILTERS, {}),
            endpoints=endpoints,
        )

    def get_endpoint(self, endpoint_name: str):
        return self.endpoints.get(endpoint_name)

    @property
    def version(self):
        return self.raw.get(bin_keys.VERSION)