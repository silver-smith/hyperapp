import inspect
import logging

_log = logging.getLogger(__name__)


RESOURCE_NAMES_ATTR = '__resource_names__'


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
            if RESOURCE_NAMES_ATTR not in module.__dict__:
                module.__dict__[RESOURCE_NAMES_ATTR] = {}
            module.__dict__[RESOURCE_NAMES_ATTR][attr_name] = full_name


param = Marker('param')
service = Marker('service')
