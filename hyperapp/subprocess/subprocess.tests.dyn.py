import logging

from .code.subprocess_tests_aux import process_main
from .tested.code import subprocess

log = logging.getLogger(__name__)


def _test_subprocess():
    main_ref = partial_ref(process_main, name='test-subprocess-main')
    with subprocess_running('test-subprocess', main_ref) as process:
        log.info("Started %r", process)
