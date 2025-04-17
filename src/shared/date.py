import datetime

DATEFORMAT = "%Y-%m-%dT%H:%M:%SZ"


def seconds_to_time(s):
    return str(datetime.timedelta(seconds=int(s)))


def iso8601_to_datetime(date):
    # for compatibility with old benchmarks
    date = date.replace("Z", "+00:00") if date.endswith("Z") else date

    return datetime.datetime.fromisoformat(date)


def get_current_datetime():
    return datetime.datetime.now(datetime.timezone.utc)


def get_current_timestamp():
    return get_current_datetime().timestamp()


def get_current_datetime_str():
    return get_current_datetime().isoformat()


def unix_ts_to_datetime(ts):
    return datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)


def unix_ts_to_datetime_str(ts):
    return unix_ts_to_datetime(ts).isoformat()
