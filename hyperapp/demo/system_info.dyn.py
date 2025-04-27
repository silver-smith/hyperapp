import os
import sys

from . import htypes
from .code.mark import mark


@mark.global_command
def system_info():
    interfaces = ', '.join(os.listdir('/sys/class/net/'))
    return [
        htypes.system_info.item('host', os.uname().nodename),
        htypes.system_info.item('python', sys.executable),
        htypes.system_info.item('interfaces', interfaces),
        ]
