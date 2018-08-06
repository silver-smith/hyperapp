import logging
import logging.config
import os
from pathlib import Path

import yaml

log = logging.getLogger(__name__)


LOGGING_CONFIG_ENV_KEY = 'LOG_CFG'
HYPERAPP_DIR = Path(__file__).parent.joinpath('../..').resolve()
CONFIG_DIR = HYPERAPP_DIR / 'log-config'


def init_logging(default_config_name):
    config_path = os.environ.get(LOGGING_CONFIG_ENV_KEY)
    if config_path:
        config_path = Path(config_path).expanduser()
        if not config_path.is_absolute():
            config_path = CONFIG_DIR / config_path
    if not config_path:
        config_path = CONFIG_DIR / default_config_name
    if config_path.exists():
        config = yaml.load(config_path.read_text())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')
