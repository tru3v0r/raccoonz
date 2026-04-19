from datetime import datetime, timedelta


TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def now_timestamp():
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def parse_timestamp(value: str):
    return datetime.strptime(value, TIMESTAMP_FORMAT)


def build_life_delta(life: dict | None):
    if not life:
        return None

    days = life.get("days", 0)
    hours = life.get("hours", 0)
    minutes = life.get("minutes", 0)
    seconds = life.get("seconds", 0)

    for key, amount in {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }.items():
        if not isinstance(amount, int):
            raise ValueError(f"life.{key} must be an integer")
        if amount < 0:
            raise ValueError(f"life.{key} must be >= 0")

    delta = timedelta(
        days=days,
        hours=hours,
        minutes=minutes,
        seconds=seconds,
    )

    if delta.total_seconds() == 0:
        raise ValueError("life must define a duration greater than 0")

    return delta


def is_expired(timestamp: str, life_delta):
    if life_delta is None:
        return False

    created_at = parse_timestamp(timestamp)
    return datetime.now() >= created_at + life_delta