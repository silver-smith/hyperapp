from datetime import datetime

from hyperapp.common.htypes import (
    TOptional,
    TList,
    TRecord,
    TException,
    tInt,
    tString,
    ref_t
    )

from .services import (
    deduce_t,
    mosaic,
    pyobj_creg,
    reconstructors,
    )
from .tested.code import type_reconstructor


def _clean_cache(t):
    try:
        del pyobj_creg._reverse_cache[id(t)]
    except KeyError:
        pass


def _test(t):
    _clean_cache(t)
    saved_reconsnstructors = [*reconstructors]
    try:
        # Also remove existing reconstructors.
        reconstructors[:] = [type_reconstructor.type_to_piece]
        piece = pyobj_creg.actor_to_piece(t)
        resolved_t = pyobj_creg.animate(piece)
        assert resolved_t is t
    finally:
        reconstructors[:] = saved_reconsnstructors


def test_primitive():
    sample_values = [
        None,
        123,
        'sample string',
        True,
        b'xxx',
        datetime.now(),
        mosaic.put(12345),
        ]
    for value in sample_values:
        t = deduce_t(value)
        piece = pyobj_creg.actor_to_piece(t)
        resolved_t = pyobj_creg.animate(piece)
        assert resolved_t is t


def test_optional():
    t = TOptional(tInt)
    _test(t)


def test_list():
    t = TList(tInt)
    _test(t)


def test_unbased_record():
    t = TRecord('sample_module', 'sample_type', {
        'int_opt': TOptional(tInt),
        'str_list': TList(tString),
        'ref': ref_t,
      })
    _test(t)


def test_based_record():
    base_t = TRecord('sample_module', 'sample_base_type', {
        'base_int_opt': TOptional(tInt),
      })
    t = TRecord('sample_module', 'sample_type', {
        'str_list': TList(tString),
        'ref': ref_t,
      }, base=base_t)
    _test(t)


def test_unbased_exception():
    t = TException('sample_module', 'sample_type', {
        'int_opt': TOptional(tInt),
        'str_list': TList(tString),
        'ref': ref_t,
      })
    _test(t)


def test_based_exception():
    base_t = TException('sample_module', 'sample_base_type', {
        'base_int_opt': TOptional(tInt),
      })
    t = TException('sample_module', 'sample_type', {
        'str_list': TList(tString),
        'ref': ref_t,
      }, base=base_t)
    _test(t)
