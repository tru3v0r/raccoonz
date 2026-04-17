from fastapi import FastAPI, HTTPException, Request
import uvicorn


class Server:
    def __init__(
        self,
        *,
        pack,
        find_records,
        resolve_served_lang,
        merge_filters,
        clean_query_params,
        format_records_response,
        resolve_path,
    ):
        self._pack = pack
        self._find_records = find_records
        self._resolve_served_lang = resolve_served_lang
        self._merge_filters = merge_filters
        self._clean_query_params = clean_query_params
        self._format_records_response = format_records_response
        self._resolve_path = resolve_path

    def serve(
        self,
        *,
        bag_content,
        bin_name=None,
        bin_names=None,
        endpoint_name=None,
        endpoint_names=None,
        lang=None,
        port=8000,
    ):
        self._pack(bag_content)

        app = FastAPI()

        bin_filter = self._merge_filters(bin_name, bin_names)
        endpoint_filter = self._merge_filters(endpoint_name, endpoint_names)

        @app.get("/")
        def serve_root(request: Request):
            query_params = dict(request.query_params)

            effective_lang = self._resolve_served_lang(
                requested_lang=query_params.get("lang"),
                served_lang=lang,
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                query_params=query_params,
            )

            records = self._find_records(
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                lang=effective_lang,
                query_params=self._clean_query_params(query_params),
            )

            if not records:
                raise HTTPException(status_code=404, detail="No matching records")

            raw = request.query_params.get("raw") == "true"
            return self._format_records_response(records, raw=raw)

        @app.get("/{path:path}")
        def serve_path(path: str, request: Request):
            parts = [p for p in path.split("/") if p]
            query_params = dict(request.query_params)

            path_bin = parts[0] if len(parts) >= 1 else None
            path_endpoint = parts[1] if len(parts) >= 2 else None

            current_bin_filter = {path_bin} if path_bin else bin_filter
            current_endpoint_filter = {path_endpoint} if path_endpoint else endpoint_filter

            if path_bin and bin_filter is not None and path_bin not in bin_filter:
                raise HTTPException(status_code=404, detail="Bin not served")

            if path_endpoint and endpoint_filter is not None and path_endpoint not in endpoint_filter:
                raise HTTPException(status_code=404, detail="Endpoint not served")

            effective_lang = self._resolve_served_lang(
                requested_lang=query_params.get("lang"),
                served_lang=lang,
                bin_filter=current_bin_filter,
                endpoint_filter=current_endpoint_filter,
                query_params=query_params,
            )

            records = self._find_records(
                bin_filter=current_bin_filter,
                endpoint_filter=current_endpoint_filter,
                lang=effective_lang,
                query_params=self._clean_query_params(query_params),
            )

            if not records:
                raise HTTPException(status_code=404, detail="No matching records")

            raw = request.query_params.get("raw") == "true"

            if len(parts) <= 2:
                return self._format_records_response(records, raw=raw)

            field_path = parts[2:]
            resolved = []

            for item in records:
                try:
                    value = self._resolve_path(item["record"].data, field_path)
                except (KeyError, IndexError, TypeError):
                    continue

                resolved.append({
                    "bin": item["bin"],
                    "endpoint": item["endpoint"],
                    "lang": item["record"].lang,
                    "params": item["record"].params,
                    "timestamp": item["record"].timestamp,
                    "value": value,
                })

            if not resolved:
                raise HTTPException(status_code=404, detail="Field not found")

            if len(resolved) == 1:
                return resolved[0]["value"]

            return resolved

        uvicorn.run(app, host="127.0.0.1", port=port)