import pytest
from hyperapp.common.htypes import (
    tString,
    tInt,
    Field,
    TRecord,
    tEmbedded,
    EncodableEmbedded,
    DecodableEmbedded,
    )
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import dict_coders, cdr_coders


@pytest.fixture(params=['json', 'yaml', 'cdr'])
def encoding(request):
    return request.param


def test_embedded(encoding):
    t = TRecord([
        Field('something', tString),
        Field('embedded', tEmbedded),
        ], name='test_record')
    embedded_t = TRecord([
        Field('x', tString),
        Field('y', tInt),
        ], name='embedded_rec')
    embedded = embedded_t(
        x='some embedded value',
        y=12345,
        )
    value = t(
        something='some value',
        embedded=EncodableEmbedded(embedded_t, embedded),
        )
    data = packet_coders.encode(encoding, value, t)
    print('encoded data:', data)
    decoded_value = packet_coders.decode(encoding, data, t)
    assert isinstance(decoded_value.embedded, DecodableEmbedded)
    decoded_embedded = decoded_value.embedded.decode(embedded_t)
    assert isinstance(decoded_embedded, embedded_t)
    assert decoded_embedded.x == embedded.x
    assert decoded_embedded.y == embedded.y
