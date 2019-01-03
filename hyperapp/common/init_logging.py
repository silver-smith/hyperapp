import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
import multiprocessing
import threading

import pytest
import yaml

log = logging.getLogger(__name__)


LOGGING_CONFIG_ENV_KEY = 'LOG_CFG'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()
CONFIG_DIR = HYPERAPP_DIR / 'log-config'


_logger_context = ''
_logger_queue = multiprocessing.Queue()


def setup_filter():

    def filter(record):
        if not hasattr(record, 'context'):
            record.context = _logger_context
        return True

    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(filter)


def init_logging(default_config_name, context=''):
    global _logger_context

    config_path = os.environ.get(LOGGING_CONFIG_ENV_KEY)
    if config_path:
        config_path = Path(config_path).expanduser()
        if not config_path.is_absolute():
            config_path = CONFIG_DIR / config_path
    if not config_path:
        config_path = CONFIG_DIR / default_config_name
    config = yaml.load(config_path.read_text())
    logging.config.dictConfig(config)

    _logger_context = context
    setup_filter()


def init_subprocess_logger(context='subprocess'):
    global _logger_context

    handler = logging.handlers.QueueHandler(_logger_queue)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    _logger_context = context
    setup_filter()


@pytest.fixture(scope='session', autouse=True)
def logger_listening():
    root_logger = logging.getLogger()
    listener = logging.handlers.QueueListener(_logger_queue, root_logger)
    listener.start()
    try:
        yield
    finally:
        listener.enqueue_sentinel()
        listener.stop()
