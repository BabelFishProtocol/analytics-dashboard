import datetime


def get_today_start_datetime():
    return datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

def get_datetime_from_string(date_str):
    return datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')

def get_string_from_datetime(dt):
    return dt.replace(microsecond=0).isoformat()+'Z'

def get_date_from_string(date_str):
    return datetime.date.fromisoformat(date_str)
