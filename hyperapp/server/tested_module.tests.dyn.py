import logging

from . import htypes
from .tested.code import (
    tested_module,
    )

log = logging.getLogger(__name__)


def test_one():
    one = htypes.tested_module.one()
    two = tested_module.sample_fn(12345)
    log.info("Test one: tested_module=%r", tested_module)
