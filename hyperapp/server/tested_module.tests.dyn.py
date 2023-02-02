import logging

from .tested.code import (
    tested_module,
    )

log = logging.getLogger(__name__)


def test_one():
    log.info("Test one: tested_module=%r", tested_module)
