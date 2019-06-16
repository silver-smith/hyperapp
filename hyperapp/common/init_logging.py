import logging
import logging.config
import logging.handlers
import os
from pathlib import Path
import multiprocessing
import threading

import yaml

log = logging.getLogger(__name__)


LOGGING_CONFIG_ENV_KEY = 'LOG_CFG'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()
CONFIG_DIR = HYPERAPP_DIR / 'log-config'


_logger_context = ''
_subprocess_logger_queue = multiprocessing.Queue()


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

    config_name = os.environ.get(LOGGING_CONFIG_ENV_KEY) or default_config_name
    config_path = CONFIG_DIR.joinpath(config_name).with_suffix('.yaml')
    config = yaml.load(config_path.read_text())
    logging.config.dictConfig(config)

    _logger_context = context
    setup_filter()


def init_subprocess_logger(context='subprocess'):
    global _logger_context

    config = yaml.load(CONFIG_DIR.joinpath('subprocess.yaml').read_text())
    logging.config.dictConfig(config)

    handler = logging.handlers.QueueHandler(_subprocess_logger_queue)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)

    _logger_context = context
    setup_filter()


def subprocess_logger_queue():
    return _subprocess_logger_queue
