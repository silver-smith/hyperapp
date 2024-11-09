import logging

from .tested.code import subprocess

log = logging.getLogger(__name__)


def _process_main(connection, received_refs, name):
    my_name = "Subprocess test main"
    log.info("%s: Started", my_name)
    try:
        value = connection.recv()
        log.info("%s: Received: %s", my_name, value)
    except EOFError as x:
        log.info("%s: Connection EOF: %s", my_name, x)
    except ConnectionResetError as x:
        log.info("%s: Connection reset: %s", my_name, x)


def test_subprocess(partial_ref, subprocess_running):
    main_ref = partial_ref(_process_main, name='test-subprocess-main')
    with subprocess_running('test-subprocess', main_ref) as process:
        log.info("Started %r", process)
