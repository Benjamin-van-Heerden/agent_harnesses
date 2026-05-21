from datetime import datetime


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def now_time() -> str:
    return datetime.now().strftime("%H:%M")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")
