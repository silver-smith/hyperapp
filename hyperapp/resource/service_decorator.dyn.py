import inspect
import logging

from .constants import RESOURCE_NAMES_ATTR

_log = logging.getLogger(__name__)


def get_caller_module():
    frame = inspect.stack()[2].frame  # Caller of the caller.
    return inspect.getmodule(frame)


class _Marker:

    def __setattr__(self, name, value):
        module = get_caller_module()
        resource_name = f'{name}.service'
        _log.info("Mark: %s: %s -> %s (%r)", module.__name__, name, resource_name, value)
        res_name_dict = module.__dict__.setdefault(RESOURCE_NAMES_ATTR, {})
        res_name_dict[name] = resource_name

    # def __call__(self, fn):
    #     module = inspect.getmodule(fn)
    #     res_name_dict = module.__dict__.setdefault(RESOURCE_NAMES_ATTR, {})
    #     res_name_dict[fn.__name__] = f'{fn.__name__}.service'
    #     return fn

service = _Marker()
