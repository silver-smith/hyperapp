import logging

from hyperapp.boot.htypes import (
    tInt,
    tString,
    tBool,
    TOptional,
    TRecord,
    TList,
    )
from hyperapp.boot.visual_rep import VisualRepEncoder

log = logging.getLogger(__name__)


def test_visual_rep():
    rec_1_t = TRecord('test', 'record_1', {
        'int_field': tInt,
        'opt_string_field': TOptional(tString),
        })
    rec_1a = rec_1_t(123, 'abc')
    rep = VisualRepEncoder().encode(rec_1_t, rec_1a)
    rep.dump(log.info)
    rec_1b = rec_1_t(123, None)
    rep = VisualRepEncoder().encode(rec_1_t, rec_1b)
    rep.dump(log.info)

    rec_2_t = TRecord('test', 'record_2', {
        'rec_1_list': TList(rec_1_t),
        })
    rec_2a = rec_2_t([rec_1_t(123, 'abc'), rec_1_t(456, None)])
    rep = VisualRepEncoder().encode(rec_2_t, rec_2a)
    rep.dump(log.info)
    rec_2b = rec_2_t([])
    rep = VisualRepEncoder().encode(rec_2_t, rec_2b)
    rep.dump(log.info)
