def safe_path_part(value):
    forbidden = '<>:"/\\|?*'
    result = str(value)

    for char in forbidden:
        result = result.replace(char, "_")

    return result.strip() or "_"


def params_key(params):
    if not params:
        return "_"

    parts = []
    for key in sorted(params):
        safe_key = safe_path_part(key)
        safe_value = safe_path_part(params[key])
        parts.append(f"{safe_key}={safe_value}")

    return ",".join(parts)


def record_key(params, lang):
    return f"{safe_path_part(lang)}::{params_key(params)}"