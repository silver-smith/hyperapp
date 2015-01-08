from datetime import datetime
from dateutil.tz import tzutc, tzlocal


def utcnow():
    return datetime.now(tzutc())
