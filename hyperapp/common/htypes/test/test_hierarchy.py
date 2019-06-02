from collections import OrderedDict

from hyperapp.common.htypes import (
    tString,
    tInt,
    THierarchy,
    TExceptionHierarchy,
    )


def test_tclass_instantiate():
    hierarchy = THierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass', OrderedDict([
        ('some_str', tString),
        ('some_int', tInt),
        ]), verbose=True)
    rec_1 = tclass(some_str='foo', some_int=123)
    assert rec_1.some_str == 'foo'
    assert rec_1.some_int == 123
    assert rec_1[0] == 'foo'
    assert rec_1[1] == 123
    assert list(rec_1) == ['foo', 123]
    assert isinstance(rec_1, tclass)
    assert isinstance(rec_1, hierarchy)
    # should omit '_t' member
    assert rec_1._asdict() == {
        'some_str': 'foo',
        'some_int': 123,
        }
    assert repr(rec_1) == "test_tclass(some_str='foo', some_int=123)"


def test_exception_class_instantiate():
    hierarchy = TExceptionHierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass', OrderedDict([
        ('some_str', tString),
        ('some_int', tInt),
        ]), verbose=True)
    rec_1 = tclass(some_str='foo', some_int=123)
    assert rec_1.some_str == 'foo'
    assert rec_1.some_int == 123
    assert rec_1[0] == 'foo'
    assert rec_1[1] == 123
    assert list(rec_1) == ['foo', 123]
    assert isinstance(rec_1, tclass)
    assert isinstance(rec_1, hierarchy)
    # should omit '_t' member
    assert rec_1._asdict() == {
        'some_str': 'foo',
        'some_int': 123,
        }
    assert repr(rec_1) == "test_tclass(some_str='foo', some_int=123)"

    rec_2 = tclass('foo', 123)
    assert rec_2.some_str == 'foo'
    assert rec_2.some_int == 123


def test_isinstance_empty():
    hierarchy = THierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass')
    rec = tclass()
    assert isinstance(rec, tclass)
    assert isinstance(rec, hierarchy)


def test_isinstance_empty_exception():
    hierarchy = TExceptionHierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass')
    rec = tclass()
    assert isinstance(rec, tclass)
    assert isinstance(rec, hierarchy)


def test_isinstance_with_fields():
    hierarchy = THierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass', OrderedDict([
        ('some_field', tString),
        ]))
    rec = tclass(some_field='some value')
    assert isinstance(rec, tclass)
    assert isinstance(rec, hierarchy)


def test_isinstance_inherited():
    hierarchy = THierarchy('test_hierarchy')
    tclass_1 = hierarchy.register('test_tclass_1', OrderedDict([
        ('some_field_1', tString),
        ]))
    tclass_2 = hierarchy.register('test_tclass_2', base = tclass_1, fields=OrderedDict([
        ('some_field_2', tString),
        ]))
    rec_1 = tclass_1(some_field_1='some value 1')
    rec_2 = tclass_2(some_field_1='some value 1', some_field_2='some value 2')
    assert isinstance(rec_1, tclass_1)
    assert not isinstance(rec_1, tclass_2)
    assert isinstance(rec_2, tclass_1)
    assert isinstance(rec_2, tclass_2)


def test_isinstance_different_hierarchies():
    hierarchy_1 = THierarchy('test_hierarchy_1')
    hierarchy_2 = THierarchy('test_hierarchy_2')
    tclass_1 = hierarchy_1.register('test_tclass', OrderedDict([
        ('some_field', tString),
        ]))
    tclass_2 = hierarchy_2.register('test_tclass', OrderedDict([
        ('some_field', tString),
        ]))
    rec = tclass_1(some_field='some value')
    assert isinstance(rec, tclass_1)
    assert not isinstance(rec, tclass_2)
    assert isinstance(rec, hierarchy_1)
    assert not isinstance(rec, hierarchy_2)


def test_isinstance_different_classes():
    hierarchy = THierarchy('test_hierarchy')
    tclass_1 = hierarchy.register('test_tclass_1', OrderedDict([
        ('some_field', tString),
        ]))
    tclass_2 = hierarchy.register('test_tclass_2', OrderedDict([
        ('some_field', tString),
        ]))
    rec = tclass_1(some_field='some value')
    assert isinstance(rec, tclass_1)
    assert not isinstance(rec, tclass_2)
