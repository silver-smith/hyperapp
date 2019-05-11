from collections import OrderedDict
import logging

from hyperapp.common.htypes import (
    tInt,
    tString,
    tBool,
    TOptional,
    TRecord,
    TList,
    THierarchy,
    TClass,
    )
from hyperapp.common.visual_rep import VisualRepEncoder

log = logging.getLogger(__name__)


def test_visual_rep():
    rec_1_t = TRecord('record_1', OrderedDict([
        ('int_field', tInt),
        ('opt_string_field', TOptional(tString)),
        ]))
    rec_1a = rec_1_t(123, 'abc')
    rep = VisualRepEncoder().encode(rec_1_t, rec_1a)
    rep.dump(log.info)
    rec_1b = rec_1_t(123, None)
    rep = VisualRepEncoder().encode(rec_1_t, rec_1b)
    rep.dump(log.info)

    rec_2_t = TRecord('record_2', OrderedDict([
        ('rec_1_list', TList(rec_1_t)),
        ]))
    rec_2a = rec_2_t([rec_1_t(123, 'abc'), rec_1_t(456, None)])
    rep = VisualRepEncoder().encode(rec_2_t, rec_2a)
    rep.dump(log.info)
    rec_2b = rec_2_t([])
    rep = VisualRepEncoder().encode(rec_2_t, rec_2b)
    rep.dump(log.info)

    hierarchy = THierarchy('test_hierarchy')
    class_1 = TClass(hierarchy, 'class_1', OrderedDict([
        ('bool_opt', TOptional(tBool)),
        ]))
    class_2 = TClass(hierarchy, 'class_1', OrderedDict([
        ('int_list', TList(tInt)),
        ]), base=class_1)
    value_1 = class_1(True)
    rep = VisualRepEncoder().encode(hierarchy, value_1)
    rep.dump(log.info)
    value_2 = class_2(None, [1, 2, 3])
    rep = VisualRepEncoder().encode(hierarchy, value_2)
    rep.dump(log.info)
