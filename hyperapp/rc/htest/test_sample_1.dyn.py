import logging

from .code.mark import mark
from .tested.code import sample_service_1 as sample_service_module_1

log = logging.getLogger(__name__)


def test_sample_service(sample_value_service_1, sample_fn_service_1):
    value_2 = sample_fn_service_1('val-1', 'val-2')
    log.info("test_sample_1: service_1=%r service_2-value=%r", sample_value_service_1.value, value_2)
