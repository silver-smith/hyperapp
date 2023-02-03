import logging

from . import htypes

log = logging.getLogger(__name__)


def sample_fn(some_arg):
    log.info("sample_fn: %s", some_arg)
    return htypes.tested_module.two()


log.info("Tested module")
