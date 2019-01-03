import logging
import logging.config
import os
from pathlib import Path

import yaml

log = logging.getLogger(__name__)


LOGGING_CONFIG_ENV_KEY = 'LOG_CFG'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()
CONFIG_DIR = HYPERAPP_DIR / 'log-config'


_logging_context = ''


def setup_filter():

    def filter(record):
        record.context = _logging_context
        return True

    for handler in logging.getLogger().handlers:
        handler.addFilter(filter)


def init_logging(default_config_name, context=''):
    global _logging_context

    config_path = os.environ.get(LOGGING_CONFIG_ENV_KEY)
    if config_path:
        config_path = Path(config_path).expanduser()
        if not config_path.is_absolute():
            config_path = CONFIG_DIR / config_path
    if not config_path:
        config_path = CONFIG_DIR / default_config_name
    config = yaml.load(config_path.read_text())
    logging.config.dictConfig(config)

    _logging_context = context
    setup_filter()
