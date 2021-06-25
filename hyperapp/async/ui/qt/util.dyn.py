import asyncio
import logging
import pickle
import weakref
from datetime import datetime
from io import StringIO

from dateutil.tz import tzutc
from PySide2 import QtCore, QtWidgets

from hyperapp.common.util import is_iterable_inst

log = logging.getLogger(__name__)


DEBUG_FOCUS = False
DEBUG_EVENTS = False


def call_after(fn, *args, **kw):
    ## print 'call_after', fn, args, kw
    QtCore.QTimer.singleShot(0, lambda: fn(*args, **kw))

def uni2str(v):
    if isinstance(v, str):
        return v.encode('utf-8')
    else:
        return v

def utcnow():
    return datetime.now(tzutc())

def key_match(evt, key_str):
    tokens = key_str.split('+')
    mods = tokens[:-1]
    key = getattr(QtCore.Qt, 'Key_' + tokens[-1], None)
    assert key, 'Invalid key: %r' % tokens[-1]
    for mod in mods:
        assert mod in ['Shift', 'Ctrl', 'Alt'], 'Invalid modifier: %r' % mod
    ## print '*** key_match', evt.key() == key if evt.type() == QtCore.QEvent.Type.KeyPress else '-' 
    if evt.type() != QtCore.QEvent.Type.KeyPress or evt.key() != key:
        return False
    for mod_id, mod_name in [
        (QtCore.Qt.ShiftModifier, 'Shift'),
        (QtCore.Qt.ControlModifier, 'Ctrl'),
        (QtCore.Qt.AltModifier, 'Alt'),
        ]:
        if (mod_name in mods) ^ bool(evt.modifiers() & mod_id):
            ## print '** no mod:', mod_name, mod_id, bool(evt.modifiers() & mod_id), mod_name in mods
            return False
    return True

def key_match_any(evt, keys):
    for key in keys:
        if key_match(evt, key):
            return True
    return False


def focused_index(parent, children, default=None):
    if parent:
        w = parent.focusWidget()
    else:
        w = QtWidgets.QApplication.focusWidget()
    while w:
        for idx, trg in enumerate(children):
            if w is trg: return idx
        w = w.parent()
    return default
    
