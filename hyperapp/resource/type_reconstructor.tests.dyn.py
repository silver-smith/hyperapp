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
        reverse_t = pyobj_creg.animate(piece)
        assert reverse_t is t


def test_optional():
    reconstructors.append(type_reconstructor.type_to_piece)
    t = TOptional(tInt)
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t


def test_list():
    reconstructors.append(type_reconstructor.type_to_piece)
    t = TList(tInt)
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t


def test_unbased_record():
    reconstructors.append(type_reconstructor.type_to_piece)
    t = TRecord('sample_module', 'sample_type', {
        'int_opt': TOptional(tInt),
        'str_list': TList(tString),
        'ref': ref_t,
      })
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t


def test_based_record():
    reconstructors.append(type_reconstructor.type_to_piece)
    base_t = TRecord('sample_module', 'sample_base_type', {
        'base_int_opt': TOptional(tInt),
      })
    t = TRecord('sample_module', 'sample_type', {
        'str_list': TList(tString),
        'ref': ref_t,
      }, base=base_t)
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t


def test_unbased_exception():
    reconstructors.append(type_reconstructor.type_to_piece)
    t = TException('sample_module', 'sample_type', {
        'int_opt': TOptional(tInt),
        'str_list': TList(tString),
        'ref': ref_t,
      })
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t


def test_based_exception():
    reconstructors.append(type_reconstructor.type_to_piece)
    base_t = TException('sample_module', 'sample_base_type', {
        'base_int_opt': TOptional(tInt),
      })
    t = TException('sample_module', 'sample_type', {
        'str_list': TList(tString),
        'ref': ref_t,
      }, base=base_t)
    piece = pyobj_creg.actor_to_piece(t)
    reverse_t = pyobj_creg.animate(piece)
    assert reverse_t is t
