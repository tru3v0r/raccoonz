import yaml
from ..record import Record
from ..constants import config
from datetime import datetime


class FileSystemStorage:
    def __init__(self, nest_root):
        self.nest_root = nest_root



    def pack(self, bag):

        if not self.nest_root.exists():
            return bag
        
        for bin_dir in self.nest_root.iterdir():
            if not bin_dir.is_dir():
                continue

            bin_name = bin_dir.name

            for lang_dir in bin_dir.iterdir():
                if not lang_dir.is_dir():
                    continue

                lang = lang_dir.name

                for endpoint_dir in lang_dir.iterdir():
                    if not endpoint_dir.is_dir():
                        continue

                    endpoint = endpoint_dir.name
                    data_dir = endpoint_dir / config.NEST_PATH_DATA
                    raw_dir = endpoint_dir / config.NEST_PATH_RAW

                    if not data_dir.exists():
                        continue

                    for data_file in data_dir.glob("*.yaml"):
                        if data_file.parent.name == "_expired":
                            continue

                        record = self._load_record(
                            data_file,
                            raw_dir,
                            default_lang=lang,
                            default_params={}
                        )

                        self._store_record(bag, bin_name, endpoint, record)
        
        return bag



    def pack_one(self, bag, bin_name, endpoint, *, lang, **params):
        record_key = self._record_key(params, lang)

        if bin_name in bag and endpoint in bag[bin_name] and record_key in bag[bin_name][endpoint]:
            return bag

        raw_dir = self._raw_dir_endpoint(bin_name, lang, endpoint)
        data_dir = self._data_dir_endpoint(bin_name, lang, endpoint)

        params_key = self._params_key(params)
        pattern = f"{params_key}.yaml"

        if not data_dir.exists():
            return bag

        data_files = [p for p in data_dir.glob(pattern) if p.is_file()]
        if not data_files:
            return bag

        data_file = data_files[0]

        record = self._load_record(
            data_file,
            raw_dir,
            default_lang=lang,
            default_params=params
        )

        self._store_record(bag, bin_name, endpoint, record)

        return bag



    def hoard(self, bin_name, endpoint, record, *, bin_version=None, bin_hash=None):
        raw_dir = self._raw_dir_endpoint(bin_name, record.lang, endpoint)
        data_dir = self._data_dir_endpoint(bin_name, record.lang, endpoint)

        raw_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        raw_expired_dir = raw_dir / config.NEST_PATH_EXPIRED
        data_expired_dir = data_dir / config.NEST_PATH_EXPIRED
        raw_expired_dir.mkdir(exist_ok=True)
        data_expired_dir.mkdir(exist_ok=True)

        stem = self._params_key(record.params)

        raw_path = raw_dir / f"{stem}.html"
        data_path = data_dir / f"{stem}.yaml"

        if data_path.exists():
            data_path.rename(data_expired_dir / f"{stem}_{self._timestamp()}.yaml")

        if raw_path.exists():
            raw_path.rename(raw_expired_dir / f"{stem}_{self._timestamp()}.html")

        if record.html is not None:
            raw_path.write_text(record.html, encoding=config.FILE_ENCODING_UTF8)

        payload = {
            config.NEST_FIELD_META: {
                config.NEST_FIELD_BIN: bin_name,
                config.NEST_FIELD_VERSION: bin_version,
                config.NEST_FIELD_HASH: bin_hash,
                config.NEST_FIELD_ENDPOINT: endpoint,
                config.NEST_FIELD_LANG: record.lang,
                config.NEST_FIELD_PARAMS: record.params,
                config.NEST_FIELD_TIMESTAMP: record.timestamp,
                config.NEST_FIELD_URL: record.url,
            },
            config.NEST_FIELD_DATA: record.data,
        }

        with data_path.open("w", encoding=config.FILE_ENCODING_UTF8) as f:
            yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)


    
    def _load_record(self, data_file, raw_dir, default_lang=None, default_params=None):
        with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
            payload = yaml.safe_load(f) or {}

        meta = payload.get(config.NEST_FIELD_META, {})
        data = payload.get(config.NEST_FIELD_DATA)

        params = meta.get(config.NEST_FIELD_PARAMS, default_params or {})
        timestamp = meta.get(config.NEST_FIELD_TIMESTAMP)
        url = meta.get(config.NEST_FIELD_URL)
        lang = meta.get(config.NEST_FIELD_LANG, default_lang)

        params_key = self._params_key(params)
        raw_file = raw_dir / f"{params_key}.html"
        html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8) if raw_file.exists() else None

        return Record(
            params=params,
            url=url,
            html=html,
            data=data,
            timestamp=timestamp,
            lang=lang,
        )
    


    def _store_record(self, bag, bin_name, endpoint, record):
        if bin_name not in bag:
            bag[bin_name] = {}
        if endpoint not in bag[bin_name]:
            bag[bin_name][endpoint] = {}

        record_key = self._record_key(record.params, record.lang)
        bag[bin_name][endpoint][record_key] = record


    def _bin_dir(self, bin_name):
        return self.nest_root / bin_name



    def _lang_dir(self, bin_name, lang):
        return self._bin_dir(bin_name) / self._safe_path_part(lang)



    def _endpoint_dir(self, bin_name, lang, endpoint):
        return self._lang_dir(bin_name, lang) / endpoint



    def _raw_dir_endpoint(self, bin_name, lang, endpoint):
        return self._endpoint_dir(bin_name, lang, endpoint) / config.NEST_PATH_RAW



    def _data_dir_endpoint(self, bin_name, lang, endpoint):
        return self._endpoint_dir(bin_name, lang, endpoint) / config.NEST_PATH_DATA



    def _params_key(self, params):
        if not params:
            return "_"

        parts = []
        for key in sorted(params):
            safe_key = self._safe_path_part(key)
            safe_value = self._safe_path_part(params[key])
            parts.append(f"{safe_key}={safe_value}")

        return ",".join(parts)


    def _record_key(self, params, lang):
        return f"{self._safe_path_part(lang)}::{self._params_key(params)}"


    def _safe_path_part(self, value):
        forbidden = '<>:"/\\|?*'
        result = str(value)

        for char in forbidden:
            result = result.replace(char, "_")

        return result.strip() or "_"


    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    