import datetime


def datetime_from_timestamp(timestamp: int):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)

