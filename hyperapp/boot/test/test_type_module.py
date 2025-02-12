import os.path
from pathlib import Path
import pytest

from hyperapp.boot.htypes import (
    tInt,
    tString,
    tBool,
    tDateTime,
    TOptional,
    TRecord,
    TException,
    TList,
    ref_t,
    )
from hyperapp.boot import cdr_coders  # register codec
from hyperapp.boot.type_module_loader import CircularDepError
from hyperapp.boot.project import load_texts
from hyperapp.boot.test.hyper_types_namespace import HyperTypesNamespace


TEST_MODULES_DIR = Path(__file__).parent.resolve()


@pytest.fixture
def types():
    return {}


@pytest.fixture
def htypes(pyobj_creg, types):
    return HyperTypesNamespace(pyobj_creg, types)


@pytest.fixture
def load_type_modules(type_module_loader, types):
    def load(dir):
        path_to_text = load_texts(dir)
        type_module_loader.load_texts(path_to_text, types)
    return load


def test_type_module_loader(load_type_modules):
    load_type_modules(TEST_MODULES_DIR / 'test_type_modules')


def test_circular_type_dep(load_type_modules):
    with pytest.raises(CircularDepError) as excinfo:
        load_type_modules(TEST_MODULES_DIR / 'circular_type_dep')
    assert str(excinfo.value) == 'Circular type module dependency: module_1->module_2->module_3->module_1'


def test_types(load_type_modules, htypes):
    load_type_modules(TEST_MODULES_DIR / 'test_type_modules')

    assert htypes.type_module_1.record_1 == TRecord('type_module_1', 'record_1', {'int_field': tInt})
    assert htypes.type_module_1.record_2 == TRecord('type_module_1', 'record_2', {'int_field': tInt, 'string_field': tString})

    assert (htypes.type_module_2.record_3 ==
            TRecord('type_module_2', 'record_3', {'int_field': tInt, 'string_field': tString, 'datetime_field': tDateTime}))
    assert htypes.type_module_2.record_with_ref == TRecord('type_module_2', 'record_with_ref', {'ref_field': ref_t})
    assert htypes.type_module_2.record_with_opt_ref == TRecord('type_module_2', 'record_with_opt_ref', {'opt_ref_field': TOptional(ref_t)})

    assert htypes.type_module_1.empty_record_1.name == 'empty_record_1'
    assert htypes.type_module_2.empty_record_2.name == 'empty_record_2'
    assert htypes.type_module_1.empty_record_1 != htypes.type_module_2.empty_record_2


def test_same_instance(load_type_modules, htypes):
    load_type_modules(TEST_MODULES_DIR / 'same_instance')

    element = htypes.same_instance.element('abcd')

    # Same types should resolve to same instances.
    assert htypes.same_instance.container.fields['element_field'] == htypes.same_instance.element
    assert htypes.same_instance.container.fields['element_field'] is htypes.same_instance.element
    # To be able to pass isinstance check on instantiation.
    value = htypes.same_instance.container(element_field=element)

    assert htypes.same_instance.list_container.fields['element_field'].element_t is htypes.same_instance.element
    value = htypes.same_instance.list_container(element_field=[element])

    assert htypes.same_instance.opt_container.fields['element_field'].base_t is htypes.same_instance.element
    value = htypes.same_instance.opt_container(element_field=element)

    assert htypes.same_instance.based_container.base is htypes.same_instance.container
    value = htypes.same_instance.based_container(element_field=element)
    assert isinstance(value, htypes.same_instance.container)


def test_exception_type(load_type_modules, htypes):
    load_type_modules(TEST_MODULES_DIR / 'test_type_modules')

    assert htypes.exceptions.exception_1 == TException('exceptions', 'exception_1', {'int_field': tInt})
    assert htypes.exceptions.exception_2 == TException('exceptions', 'exception_2', {'int_field': tInt, 'string_field': tString})
    assert htypes.exceptions.empty_exception == TException('exceptions', 'empty_exception', {})
