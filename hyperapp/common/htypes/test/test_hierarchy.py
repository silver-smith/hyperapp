from hyperapp.common.htypes import (
    tString,
    Field,
    THierarchy,
    )


def test_hierarchy_isinstance_empty():
    hierarchy = THierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass')
    rec = tclass()
    assert isinstance(rec, tclass)
    assert isinstance(rec, hierarchy)


def test_hierarchy_isinstance_with_fields():
    hierarchy = THierarchy('test_hierarchy')
    tclass = hierarchy.register('test_tclass', [
        Field('some_field', tString),
        ])
    rec = tclass(some_field='some value')
    assert isinstance(rec, tclass)
    assert isinstance(rec, hierarchy)


def test_hierarchy_isinstance_inherited():
    hierarchy = THierarchy('test_hierarchy')
    tclass_1 = hierarchy.register('test_tclass_1', [
        Field('some_field_1', tString),
        ])
    tclass_2 = hierarchy.register('test_tclass_2', base = tclass_1, fields=[
        Field('some_field_2', tString),
        ])
    rec_1 = tclass_1(some_field_1='some value 1')
    rec_2 = tclass_2(some_field_1='some value 1', some_field_2='some value 2')
    assert isinstance(rec_1, tclass_1)
    assert not isinstance(rec_1, tclass_2)
    assert isinstance(rec_2, tclass_1)
    assert isinstance(rec_2, tclass_2)


def test_hierarchy_isinstance_different_hierarchies():
    hierarchy_1 = THierarchy('test_hierarchy_1')
    hierarchy_2 = THierarchy('test_hierarchy_2')
    tclass_1 = hierarchy_1.register('test_tclass', [
        Field('some_field', tString),
        ])
    tclass_2 = hierarchy_2.register('test_tclass', [
        Field('some_field', tString),
        ])
    rec = tclass_1(some_field='some value')
    assert isinstance(rec, tclass_1)
    assert not isinstance(rec, tclass_2)
    assert isinstance(rec, hierarchy_1)
    assert not isinstance(rec, hierarchy_2)


def test_hierarchy_isinstance_different_classes():
    hierarchy = THierarchy('test_hierarchy')
    tclass_1 = hierarchy.register('test_tclass_1', [
        Field('some_field', tString),
        ])
    tclass_2 = hierarchy.register('test_tclass_2', [
        Field('some_field', tString),
        ])
    rec = tclass_1(some_field='some value')
    assert isinstance(rec, tclass_1)
    assert not isinstance(rec, tclass_2)
