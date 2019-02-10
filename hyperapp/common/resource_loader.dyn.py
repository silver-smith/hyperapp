import re
import yaml
import logging

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.ref import ref_repr
from hyperapp.common.module import Module
from . import htypes

log = logging.getLogger(__name__)

MODULE_NAME = 'resource_loader'


class ResourceLoader(object):

    def __init__(self, ref_registry, local_code_module_registry, resource_registry):
        self._ref_registry = ref_registry
        self._local_code_module_registry = local_code_module_registry
        self._resource_registry = resource_registry

    def load_resources_from_dir(self, dir):
        for fpath in dir.glob('*.resources.*.yaml'):
            module_name, locale = re.match(r'(.+)\.resources\.([^.]+)\.yaml', fpath.name).groups()
            full_module_name = 'client.' + module_name
            try:
                code_module_ref = self._local_code_module_registry[full_module_name]
            except KeyError:
                log.warning('Skipping %r resource because code module %r is missing (file path: "%s")', module_name, module_name, fpath)
                continue
            log.info('Loading %r %r resources from %s "%s"', module_name, locale, ref_repr(code_module_ref), fpath)
            self._load_resources_from_file(locale, code_module_ref, fpath)

    def _load_resources_from_file(self, locale, code_module_ref, fpath):
        with fpath.open() as f:
            object_items = yaml.load(f)
            for object_id, sections in object_items.items():
                for section_type, item_elements in sections.items():
                    self._load_resource_section(section_type, locale, code_module_ref, object_id, item_elements)

    def _load_resource_section(self, section_type, locale, code_module_ref, object_id, item_elements):
        for item_id, items in item_elements.items():
            if section_type == 'commands':
                resource = self._value2command_resource(items)
                item_type = 'command'
            elif section_type == 'columns':
                resource = self._value2column_resource(items)
                item_type = 'column'
            else:
                assert False, 'Unknown resource section type: %r' % section_type
            resource_ref = self._ref_registry.register_object(resource)
            resource_key = resource_key_t(code_module_ref, [item_type, object_id, item_id])
            self._resource_registry.register(resource_key, locale, resource_ref)

    def _value2command_resource(self, value):
        return htypes.resource.command_resource(
            is_default=value.get('is_default', False),
            text=value.get('text'),
            description=value.get('description') or value.get('text'),
            shortcut_list=value.get('shortcuts', []),
            )

    def _value2column_resource(self, value):
        return htypes.resource.column_resource(
            is_visible=value.get('visible', True),
            text=value.get('text'),
            description=value.get('description'),
            )


class ThisModule(Module):

    def __init__(self, services):
        super().__init__(MODULE_NAME)
        self._resource_loader = ResourceLoader(services.ref_registry, services.local_code_module_registry, services.resource_registry)
        self._client_resources_dir = services.client_resources_dir

    def init_phase_2(self, services):
        self._resource_loader.load_resources_from_dir(self._client_resources_dir)
