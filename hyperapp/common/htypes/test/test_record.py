from hyperapp.common.htypes import (
    tString,
    tInt,
    TOptional,
    TList,
    TRecord,
    ref_t,
    )


def test_instantiate():
    t = TRecord('test', 'test_record', {
        'some_str': tString,
        'some_int': tInt,
        }, verbose=True)
    rec_1 = t(some_str='foo', some_int=123)
    assert rec_1.some_str == 'foo'
    assert rec_1.some_int == 123
    assert rec_1[0] == 'foo'
    assert rec_1[1] == 123
    assert list(rec_1) == ['foo', 123]
    assert rec_1._asdict() == {
        'some_str': 'foo',
        'some_int': 123,
        }
    assert repr(rec_1) == "test.test_record(some_str='foo', some_int=123)"
    assert rec_1._replace(some_int=456) == t(some_str='foo', some_int=456)

    rec_2 = t('foo', 123)
    assert rec_1 == rec_2
    # should omit '_t' member


def test_instantiate_empty():
    t = TRecord('test', 'test_record', {}, verbose=True)
    rec_1 = t()
    assert list(rec_1) == []
    assert rec_1._asdict() == {}
    assert repr(rec_1) == "test.test_record()"

    rec_2 = t()
    assert rec_1 == rec_2


def test_record_repr():
    t = TRecord('test', 'test', {
        'field_1': tString,
        'field_2': tInt,
        })
    assert repr(t('abc', 123)) == "test.test(field_1='abc', field_2=123)"


def test_empty_record_repr():
    empty_t = TRecord('test', 'empty')
    assert repr(empty_t()) == "test.empty()"


def test_ref_str():
    ref = ref_t('test_algorithm', b'3U')
    assert str(ref) == 'test_algorithm:3355'


def test_ref_repr():
    ref = ref_t('test_algorithm', b'3U')
    assert repr(ref) == 'ref(test_algorithm:3355)'


def test_is_instance_primitives():
    t = TRecord('test', 'test_record', {
        'str_field': tString,
        'int_field': tInt,
        })
    assert isinstance(t('abc', 123), t)


def test_is_instance_ref_opt():
    t = TRecord('test', 'test_record', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    assert isinstance(t('abc', None), t)


def test_is_instance_list():
    element_t = TRecord('test', 'test_element', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    t = TRecord('test', 'test_record', {
        'element_list': TList(element_t),
        })
    element = element_t('abc', None)
    value = t(element_list=(element,))
    assert isinstance(value, t)


def test_is_instance_base_list():
    element_t = TRecord('test', 'test_element', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    base_t = TRecord('test', 'test_base', {
        'element_list': TList(element_t),
        })
    t = TRecord('test', 'test_record', base=base_t)
    element = element_t('abc', None)
    value = t(element_list=(element,))
    assert isinstance(value, t)
