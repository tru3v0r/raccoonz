from dataclasses import dataclass, field
from typing import Any

from ..constants import bin_keys
from ..constants import config
from ..errors import BinValidationError, EndpointValidationError
from ..utils.time import build_life_delta


@dataclass(frozen=True)
class Endpoint:
    name: str
    path: str | None
    fields: dict[str, Any] = field(default_factory=dict)
    life: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, *, bin_name: str, name: str, data: dict[str, Any]):
        if not isinstance(data, dict):
            raise EndpointValidationError(
                bin_name,
                name,
                detail="Endpoint config must be a mapping.",
            )

        path = data.get(bin_keys.ENDPOINT_PATH)
        if not path:
            raise EndpointValidationError(
                bin_name,
                name,
                detail=f"Missing required key '{bin_keys.ENDPOINT_PATH}'.",
            )

        if not isinstance(path, str):
            raise EndpointValidationError(
                bin_name,
                name,
                detail=f"'{bin_keys.ENDPOINT_PATH}' must be a string.",
            )

        fields = data.get(bin_keys.FIELDS, {})
        if not isinstance(fields, dict):
            raise EndpointValidationError(
                bin_name,
                name,
                detail=f"'{bin_keys.FIELDS}' must be a mapping.",
            )

        life = data.get(bin_keys.ENDPOINT_LIFE, {})
        if not isinstance(life, dict):
            raise EndpointValidationError(
                bin_name,
                name,
                detail=f"'{bin_keys.ENDPOINT_LIFE}' must be a mapping.",
            )

        try:
            build_life_delta(life if life else None)
        except ValueError as e:
            raise EndpointValidationError(
                bin_name,
                name,
                detail=str(e),
            )

        return cls(
            name=name,
            path=path,
            fields=fields,
            life=life,
        )

    @property
    def life_delta(self):
        return build_life_delta(self.life if self.life else None)



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
        if not isinstance(raw, dict):
            raise BinValidationError(
                "<unknown>",
                detail="Bin content must be a mapping.",
            )

        bin_name = raw.get(bin_keys.NAME) or "<unnamed>"

        url = raw.get(bin_keys.URL)
        if not url:
            raise BinValidationError(
                bin_name,
                detail=f"Missing required key '{bin_keys.URL}'.",
            )

        if not isinstance(url, str):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.URL}' must be a string.",
            )

        fetcher = raw.get(bin_keys.FETCHER, config.DEFAULT_FETCHER)
        if not isinstance(fetcher, str):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.FETCHER}' must be a string.",
            )

        parser = raw.get(bin_keys.PARSER, config.DEFAULT_PARSER)
        if not isinstance(parser, str):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.PARSER}' must be a string.",
            )

        fetch = raw.get(bin_keys.FETCH, {})
        if not isinstance(fetch, dict):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.FETCH}' must be a mapping.",
            )

        filters = raw.get(bin_keys.FILTERS, {})
        if not isinstance(filters, dict):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.FILTERS}' must be a mapping.",
            )

        endpoints_raw = raw.get(bin_keys.ENDPOINTS)
        if endpoints_raw is None:
            raise BinValidationError(
                bin_name,
                detail=f"Missing required key '{bin_keys.ENDPOINTS}'.",
            )

        if not isinstance(endpoints_raw, dict):
            raise BinValidationError(
                bin_name,
                detail=f"'{bin_keys.ENDPOINTS}' must be a mapping.",
            )

        endpoints = {
            endpoint_name: Endpoint.from_dict(
                bin_name=bin_name,
                name=endpoint_name,
                data=endpoint_data,
            )
            for endpoint_name, endpoint_data in endpoints_raw.items()
        }

        return cls(
            name=bin_name,
            hash=hash_value,
            raw=raw,
            url=url,
            fetcher=fetcher,
            parser=parser,
            fetch=fetch,
            filters=filters,
            endpoints=endpoints,
        )

    def get_endpoint(self, endpoint_name: str):
        return self.endpoints.get(endpoint_name)

    @property
    def version(self):
        return self.raw.get(bin_keys.VERSION)