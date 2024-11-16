from collections import defaultdict
from operator import attrgetter

from . import htypes
from .services import (
    mosaic,
    resource_module_factory,
    )
from .code.config_ctl import service_pieces_to_config
from .code.config_item_resource import ConfigItemResource
from .code.rc_target import Target


class ConfigResourceTarget(Target):

    @staticmethod
    def target_name():
        return 'config'

    def __init__(self, custom_resource_registry, resource_dir, module_name, path):
        self._service_to_targets = defaultdict(set)
        self._req_to_service_target = defaultdict(set)
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

    def add_item(self, service, item_tgt, req):
        self._service_to_targets[service].add(item_tgt)
        if req:
            self._req_to_service_target[req] = (service, item_tgt)

    def ready_req_to_resources(self):
        req_to_resources = defaultdict(set)
        for req, (service_name, target) in self._req_to_service_target.items():
            if not target.completed:
                continue
            resource = ConfigItemResource(
                service_name=service_name,
                template_ref=mosaic.put(target.resource),
                )
            req_to_resources[req].add(resource)
        return dict(req_to_resources)

    def get_output(self):
        resource_module = resource_module_factory(
            self._custom_resource_registry, self._module_name, resource_dir=self._resource_dir)
        service_to_config_piece = {}
        for service_name, target_set in sorted(self._service_to_targets.items()):
            item_list = [
                target.resource
                for target in target_set
                if target.completed
                ]
            if not item_list:
                continue
            sorted_item_list = sorted(item_list, key=self._sort_key)
            service_config = self._items_to_data(sorted_item_list)
            resource_module[service_name] = service_config
            service_to_config_piece[service_name] = service_config
        config = service_pieces_to_config(service_to_config_piece)
        resource_module['config'] = config
        return (self._path, resource_module.as_text)

    @staticmethod
    def _items_to_data(item_list):
        return htypes.system.item_list_config(
            items=tuple(
                mosaic.put(item)
                for item in item_list
                ),
            )

    def _sort_key(self, resource):
        return self._custom_resource_registry.reverse_resolve(resource)
