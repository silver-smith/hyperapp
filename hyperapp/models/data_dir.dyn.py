from pathlib import Path

from .code.mark import mark
from .code.record_config import RecordConfigCtl


@mark.service(ctl=RecordConfigCtl())
def data_dir(config):
    return Path(config.data_dir).expanduser()
