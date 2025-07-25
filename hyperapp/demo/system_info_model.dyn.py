import os
import sys

from . import htypes
from .code.mark import mark


@mark.model
def system_info(piece):
    interfaces = ', '.join(os.listdir('/sys/class/net/'))
    return [
        htypes.system_info.item('host', os.uname().nodename),
        htypes.system_info.item('python', sys.executable),
        htypes.system_info.item('interfaces', interfaces),
        ]


@mark.global_command
def open_system_info():
    return htypes.system_info_model.model()
