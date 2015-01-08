from datetime import datetime
from dateutil.tz import tzutc, tzlocal


def utcnow():
    return datetime.now(tzutc())

def str2id( s ):
    if s == 'new':
        return None
    else:
        return int(s)

def id2str( id ):
    if id is None:
        return 'new'
    else:
        return str(id)
