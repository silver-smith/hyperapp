import logging

from .services import (
    partial_ref,
    )
from .code.subprocess_2_tests_aux import process_main
from .tested.services import subprocess_running_2

log = logging.getLogger(__name__)


def test_subprocess():
    main_ref = partial_ref(process_main, name='test-subprocess-main')
    with subprocess_running_2('test-subprocess', main_ref) as process:
        log.info("Started %r", process)
