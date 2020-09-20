from collections import OrderedDict

import pytest

from hyperapp.common.htypes import (
    tString,
    tInt,
    TRecord,
    tEmbedded,
    EncodableEmbedded,
    DecodableEmbedded,
    )
from hyperapp.common.htypes.packet_coders import packet_coders
from hyperapp.common import cdr_coders
from hyperapp.common.services import ServicesBase


code_module_list = [
    'common.dict_coders',
    ]


class Services(ServicesBase):

    def __init__(self):
        super().__init__()
        try:
            self.init_services()
            self._load_code_module_list(code_module_list)
            self.module_registry.init_phases(self)
        except:
            self.stop()
            raise

    def schedule_stopping(self):
        self.stop()


@pytest.fixture(autouse=True)
def services():
    services = Services()
    services.start()
    yield
    services.stop()


@pytest.fixture(params=['json', 'yaml', 'cdr'])
def encoding(request):
    return request.param


def test_embedded(encoding):
    t = TRecord('test_record', OrderedDict([
        ('something', tString),
        ('embedded', tEmbedded),
        ]))
    embedded_t = TRecord('embedded_rec', OrderedDict([
        ('x', tString),
        ('y', tInt),
        ]))
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
