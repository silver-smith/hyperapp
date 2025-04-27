import os
import sys

from . import htypes
from .code.mark import mark


@mark.global_command
def system_info():
    info = {
      'host': os.uname().nodename,
      'python': sys.executable,
      'interfaces': ', '.join(os.listdir('/sys/class/net/'))
      }
    return [
        htypes.system_info.item(name, value)
        for name, value in info.items()
        ]
