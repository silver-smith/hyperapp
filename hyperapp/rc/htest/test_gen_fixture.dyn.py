import logging
from unittest.mock import Mock

from .code.mark import mark
from .tested.code import sample_service_1 as sample_service_module_1

log = logging.getLogger(__name__)


@mark.fixture
def gen():
    yield Mock(value='gen-value')
    log.info("Gen fixture finalizer")


def test_gen(gen):
    assert gen.value == 'gen-value'
