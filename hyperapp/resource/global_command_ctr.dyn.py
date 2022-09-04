import inspect

from . import htypes
from .services import (
  mosaic,
  )
from .constants import RESOURCE_CTR_ATTR


def global_command(fn):
    module = inspect.getmodule(fn)
    ctr_dict = module.__dict__.setdefault(RESOURCE_CTR_ATTR, {})
    ctr_list = ctr_dict.setdefault(fn.__name__, [])
    ctr = htypes.global_command_ctr.global_command_ctr()
    ctr_list.append(mosaic.put(ctr))
    return fn


def construct(piece):
    assert 0
