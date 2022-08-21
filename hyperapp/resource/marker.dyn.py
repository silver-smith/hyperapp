import inspect
import logging

_log = logging.getLogger(__name__)

from .constants import RESOURCE_NAMES_ATTR


class Marker:

    def __init__(self, name):
        self._name = name

    def __getattr__(self, name):
        return Marker(f'{self._name}.{name}')

    def __setattr__(self, name, value):
        if name == '_name':
            super().__setattr__(name, value)
        else:
            frame = inspect.stack()[1].frame
            module = inspect.getmodule(frame)
            full_name = f'{self._name}.{name}'
            attr_name = full_name.replace('.', '_')
            _log.info("Mark: %s: %s/%s=%r", module.__name__, attr_name, full_name, value)
            module.__dict__[attr_name] = value
            self._set_res_name(module, attr_name, full_name)

    def __call__(self, fn):
        frame = inspect.stack()[1].frame
        module = inspect.getmodule(frame)
        self._set_res_name(module, fn.__name__, self._name)
        return fn

    def _set_res_name(self, module, attr_name, res_name):
        try:
            res_name_dict = module.__dict__[RESOURCE_NAMES_ATTR]
        except KeyError:
            res_name_dict = module.__dict__[RESOURCE_NAMES_ATTR] = {}
        res_name_dict[attr_name] = res_name


param = Marker('param')
service = Marker('service')
module = Marker('module')
