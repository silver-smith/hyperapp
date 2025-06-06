from hyperapp.boot.htypes import (
    TOptional,
    TList,
    TRecord,
    TException,
    tString,
    ref_t,
    )

from .services import (
    deduce_t,
    mosaic,
    )
from .tested.code import ref_picker


def test_ref():
    ref = mosaic.put("Sample text")
    picker = ref_picker._type_to_picker(deduce_t(ref))
    assert set(picker.pick_refs(ref)) == {ref}


def test_opt():
    t = TOptional(ref_t)
    picker = ref_picker._type_to_picker(t)
    ref = mosaic.put("Sample text")
    assert set(picker.pick_refs(ref)) == {ref}
    assert set(picker.pick_refs(None)) == set()


def test_list():
    t = TList(ref_t)
    picker = ref_picker._type_to_picker(t)
    ref_1 = mosaic.put("Sample text 1")
    ref_2 = mosaic.put("Sample text 2")
    assert set(picker.pick_refs((ref_1, ref_2))) == {ref_1, ref_2}
    assert set(picker.pick_refs(())) == set()


def test_record():
    t = TRecord('ref_picker_tests', 'test_record', {
        'some_string': tString,
        'some_ref': ref_t,
        })
    picker = ref_picker._type_to_picker(t)
    ref = mosaic.put("Sample text")
    record = t("Some string", ref)
    assert set(picker.pick_refs(record)) == {ref}


def test_one_field_record():
    t = TRecord('ref_picker_tests', 'test_one_field_record', {
        'some_ref': ref_t,
        })
    picker = ref_picker._type_to_picker(t)
    ref = mosaic.put("Sample text")
    record = t(ref)
    assert set(picker.pick_refs(record)) == {ref}


def test_exception():
    t = TException('ref_picker_tests', 'test_exception', {
        'some_string': tString,
        'some_ref': ref_t,
        })
    picker = ref_picker._type_to_picker(t)
    ref = mosaic.put("Sample text")
    record = t("Some string", ref)
    assert set(picker.pick_refs(record)) == {ref}


def test_combined():
    opt_t = TOptional(ref_t)
    list_t = TList(ref_t)
    t = TRecord('ref_picker_tests', 'test_composite_record', {
        'some_opt': opt_t,
        'some_list': list_t,
        })
    picker = ref_picker._type_to_picker(t)
    ref_1 = mosaic.put("Sample text 1")
    ref_2 = mosaic.put("Sample text 2")
    ref_3 = mosaic.put("Sample text 3")
    assert set(picker.pick_refs(t(None, ()))) == set()
    assert set(picker.pick_refs(t(ref_1, (ref_2, ref_3)))) == {ref_1, ref_2, ref_3}


def test_service(pick_refs):
    opt_t = TOptional(ref_t)
    list_t = TList(ref_t)
    t = TRecord('ref_picker_tests', 'test_service_record', {
        'some_opt': opt_t,
        'some_list': list_t,
        })
    ref_1 = mosaic.put("Sample text 1")
    ref_2 = mosaic.put("Sample text 2")
    ref_3 = mosaic.put("Sample text 3")
    assert set(pick_refs(t(None, ()), t)) == set()
    assert set(pick_refs(t(ref_1, (ref_2, ref_3)))) == {ref_1, ref_2, ref_3}
