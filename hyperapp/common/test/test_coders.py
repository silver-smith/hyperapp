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
from hyperapp.common.packet_coders import packet_coders
from hyperapp.common import dict_coders, cdr_coders


@pytest.fixture(params=['json', 'yaml', 'cdr'])
def encoding(request):
    return request.param


def test_embedded(encoding):
    t = TRecord([
        Field('something', tString),
        Field('embedded', tEmbedded),
        ])
    embedded_t = TRecord([
        Field('x', tString),
        Field('y', tInt),
        ])
    embedded = embedded_t(
        x='some embedded value',
        y=12345,
        )
    value = t(
        something='some value',
        embedded=EncodableEmbedded(embedded, embedded_t),
        )
    data = packet_coders.encode(encoding, value, t)
    print('encoded data:', data)
    decoded_value = packet_coders.decode(encoding, data, t)
    assert isinstance(decoded_value.embedded, DecodableEmbedded)
    decoded_embedded = decoded_value.embedded.decode(embedded_t)
    assert isinstance(decoded_embedded, embedded_t)
    assert decoded_embedded.x == embedded.x
    assert decoded_embedded.y == embedded.y
