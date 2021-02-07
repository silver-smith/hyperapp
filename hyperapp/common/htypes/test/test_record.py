from hyperapp.common.htypes import (
    tString,
    tInt,
    TRecord,
    ref_t,
    )


def test_instantiate():
    t = TRecord('test_record', {
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
    assert repr(rec_1) == "test_record(some_str='foo', some_int=123)"
    assert rec_1._replace(some_int=456) == t(some_str='foo', some_int=456)

    rec_2 = t('foo', 123)
    assert rec_1 == rec_2
    # should omit '_t' member


def test_instantiate_empty():
    t = TRecord('test_record', {}, verbose=True)
    rec_1 = t()
    assert list(rec_1) == []
    assert rec_1._asdict() == {}
    assert repr(rec_1) == "test_record()"

    rec_2 = t()
    assert rec_1 == rec_2


def test_ref_repr():
    t = TRecord('test', {
        'field_1': tString,
        'field_2': tInt,
        })
    assert repr(t('abc', 123)) == "test(field_1='abc', field_2=123)"

    empty_t = TRecord('empty')
    assert repr(empty_t()) == "empty()"

    ref = ref_t('test_algorithm', b'3U')
    assert repr(ref) == 'ref(test_algorithm:3355)'
