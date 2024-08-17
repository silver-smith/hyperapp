from collections import defaultdict
from operator import attrgetter

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    )
from .code.rc_target import Target


class ConfigResourceTarget(Target):

    @staticmethod
    def target_name():
        return 'config'

    def __init__(self, custom_resource_registry, resource_dir, module_name, path):
        self._service_to_targets = defaultdict(set)
        self._custom_resource_registry = custom_resource_registry
        self._resource_dir = resource_dir
        self._module_name = module_name
        self._path = path

    @property
    def name(self):
        return self.target_name()

    @property
    def completed(self):
        return True

    @property
    def has_output(self):
        return True

    def add_item(self, service, item_tgt):
        self._service_to_targets[service].add(item_tgt)

    def get_output(self):
        service_list = []
        for service_name, target_set in sorted(self._service_to_targets.items()):
            items = tuple(
                mosaic.put(target.resource)
                for target
                in sorted(target_set, key=attrgetter('name'))
                if target.completed
                )
            service_list.append(htypes.system.service_config(service_name, items))
        config = htypes.system.system_config(tuple(service_list))
        resource_module = resource_module_factory(
            self._custom_resource_registry, self._module_name, resource_dir=self._resource_dir)
        resource_module['config'] = config
        return (self._path, resource_module.as_text)
