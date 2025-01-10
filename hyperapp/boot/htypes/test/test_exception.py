from hyperapp.boot.htypes import (
    tString,
    tInt,
    TOptional,
    TList,
    TException,
    ref_t,
    )


def test_instantiate():
    t = TException('test', 'test_exception', {
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
    assert repr(rec_1) == "test_exception(some_str='foo', some_int=123)"

    rec_2 = t('foo', 123)
    assert rec_1 == rec_2
    # should omit '_t' member


def test_instantiate_empty():
    t = TException('test', 'test_exception', {}, verbose=True)
    rec_1 = t()
    assert list(rec_1) == []
    assert rec_1._asdict() == {}
    assert repr(rec_1) == "test_exception()"

    rec_2 = t()
    assert rec_1 == rec_2


def test_exception_repr():
    t = TException('test', 'test', {
        'field_1': tString,
        'field_2': tInt,
        })
    assert repr(t('abc', 123)) == "test(field_1='abc', field_2=123)"


def test_exception_str_1():
    t = TException('test', 'test', {
        'field_1': tInt,
        })
    assert str(t(123)) == "test(field_1=123)"


def test_exception_str_2():
    t = TException('test', 'test', {
        'field_1': tString,
        'field_2': tInt,
        })
    assert str(t('abc', 123)) == "test(field_1='abc', field_2=123)"


def test_empty_exception_repr():
    empty_t = TException('test', 'empty')
    assert repr(empty_t()) == "empty()"


def test_is_instance_primitives():
    t = TException('test', 'test_exception', {
        'str_field': tString,
        'int_field': tInt,
        })
    assert isinstance(t('abc', 123), t)


def test_is_instance_ref_opt():
    t = TException('test', 'test_exception', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    assert isinstance(t('abc', None), t)


def test_is_instance_list():
    element_t = TException('test', 'test_element', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    t = TException('test', 'test_exception', {
        'element_list': TList(element_t),
        })
    element = element_t('abc', None)
    value = t(element_list=(element,))
    assert isinstance(value, t)


def test_is_instance_base_list():
    element_t = TException('test', 'test_element', {
        'str_field': tString,
        'ref_field': TOptional(ref_t),
        })
    base_t = TException('test', 'test_base', {
        'element_list': TList(element_t),
        })
    t = TException('test', 'test_exception', base=base_t)
    element = element_t('abc', None)
    value = t(element_list=(element,))
    assert isinstance(value, t)
