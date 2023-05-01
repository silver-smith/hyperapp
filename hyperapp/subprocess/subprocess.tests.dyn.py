import logging

from .services import (
    partial_ref,
    )
from .code.subprocess_tests_aux import process_main
from .tested.services import subprocess_running

log = logging.getLogger(__name__)


def test_subprocess():
    main_ref = partial_ref(process_main, name='test-subprocess-main')
    with subprocess_running('test-subprocess', main_ref) as process:
        log.info("Started %r", process)
