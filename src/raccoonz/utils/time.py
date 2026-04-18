from datetime import datetime


def now_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")