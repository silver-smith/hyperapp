import logging

from .tested.services import subprocess_running_2

log = logging.getLogger(__name__)


def test_subprocess():
    with subprocess_running_2('test-subprocess') as process:
        log.info("Started %r", process)
# x
