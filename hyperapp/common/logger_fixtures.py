import logging
import logging.handlers

import pytest

from .init_logging import subprocess_logger_queue


@pytest.fixture(scope='session', autouse=True)
def logger_listening():
    root_logger = logging.getLogger()
    listener = logging.handlers.QueueListener(subprocess_logger_queue(), root_logger)
    listener.start()
    try:
        yield
    finally:
        listener.enqueue_sentinel()
        listener.stop()
