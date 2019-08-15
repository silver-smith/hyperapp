import re
import yaml
import logging

from hyperapp.common.htypes import resource_key_t
from hyperapp.common.ref import ref_repr
from hyperapp.common.dict_decoders import DictDecoder
from hyperapp.common.module import Module
from . import htypes

_log = logging.getLogger(__name__)


class ResourceLoader(object):

    def __init__(self, ref_registry, type_resolver, local_type_module_registry, local_code_module_registry, resource_registry):
        self._ref_registry = ref_registry
        self._type_resolver = type_resolver
        self._local_type_module_registry = local_type_module_registry
        self._local_code_module_registry = local_code_module_registry
        self._resource_registry = resource_registry
        self._dict_decoder = DictDecoder()

    def load_resources_from_dir(self, dir):
        for file_path in dir.glob('*.resources.*.yaml'):
            [locale] = re.match(r'.+\.resources\.([^.]+)\.yaml', file_path.name).groups()
            _log.info("Loading %r resources from '%s'", locale, file_path)
            self._load_resources_from_file(file_path, locale)

    def _load_resources_from_file(self, file_path, locale):
        with file_path.open() as f:
            file_items = yaml.safe_load(f)
            for base_path, sections in file_items.items():
                base_ref, path = self._base_path_to_ref(file_path, base_path)
                if not base_ref:
                    continue
                for section_type, section_contents in sections.items():
                    self._load_resource_section(locale, base_ref, section_type, path, section_contents)

    def _base_path_to_ref(self, file_path, base_path):
        if ':' not in base_path:
            return (None, None)  # Skip format; todo: remove when all resources are updated
        kind, base_path, *path = base_path.split(':')
        try:
            if kind == 'module':
                return (self._local_code_module_registry[base_path], path)
            if kind == 'type':
                module_name, type_name = base_path.split('.')
                return (self._local_type_module_registry[module_name][type_name], path)
            raise RuntimeError("'{}': Unknown base path kind: {!r}".format(file_path, kind))
        except KeyError:
            _log.warning("%s: Skipping resource because %s %r is unknown", file_path, kind, base_path)
            return (None, None)

    def _load_resource_section(self, locale, base_ref, section_type, path, section_contents):
        if section_type == 'layout':
            resource_ref = self._value2layout(section_contents)
            resource_key = resource_key_t(base_ref, [*path, 'layout'])
            self._resource_registry.register(resource_key, locale, resource_ref)
        elif section_type == 'layout_commands':
            resource_ref = self._value2layout_commands(section_contents)
            resource_key = resource_key_t(base_ref, [*path, 'layout_commands'])
            self._resource_registry.register(resource_key, locale, resource_ref)
        else:
            self._load_resource_section_elements(locale, base_ref, section_type, path, section_contents)

    def _load_resource_section_elements(self, locale, base_ref, section_type, path, item_elements):
        for item_id, items in item_elements.items():
            resource_ref = None
            resource = None
            if section_type == 'commands':
                resource = self._value2command_resource(items)
                item_type = 'command'
            elif section_type == 'columns':
                resource = self._value2column_resource(items)
                item_type = 'column'
            else:
                assert False, 'Unknown resource section type: %r' % section_type
            resource_ref = self._ref_registry.register_object(resource)
            resource_key = resource_key_t(base_ref, [*path, item_type, item_id])
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

    def _value2layout(self, section_contents):
        view_ref = self._value2layout_view(section_contents.get('view'))
        layout_commands = list(self._value2layout_commands(section_contents.get('commands', [])))
        layout = htypes.resource.layout(view_ref, layout_commands)
        layout_ref = self._ref_registry.register_object(layout)
        _log.debug("Loaded layout %s: %s", ref_repr(layout_ref), layout)
        return layout_ref

    def _value2layout_view(self, value):
        if not value:
            return None
        module_name, type_name = value['type'].split('.')
        type_ref = self._local_type_module_registry[module_name][type_name]
        t = self._type_resolver.resolve(type_ref)
        if value['type'] == 'record_view.record_view_layout':
            # special case for record view layout; todo: general solution, such as htype mapper or move out of resource yaml at all
            view = self._value2record_view(value['value'], t)
        else:
            view = self._dict_decoder.decode_dict(t, value.get('value', {}))
        view_ref = self._ref_registry.register_object(view, t)
        _log.debug("Loaded layout view %s: %s", ref_repr(view_ref), view)
        return view_ref

    def _value2record_view(self, value, t):
        field_layout_ref = self._local_type_module_registry['record_view']['field_layout']
        field_layout_t = self._type_resolver.resolve(field_layout_ref)
        field_list = []
        for field in value['fields']:
            view_ref = self._value2layout(field['layout'])
            field_list.append(field_layout_t(field['field_id'], view_ref))
        return t(field_list)

    def _value2layout_commands(self, value):
        for command in value:
            if 'layout' in command:
                layout_ref = self._value2layout(command['layout'])
            else:
                layout_ref = None
            yield htypes.resource.layout_command(command['command_id'], layout_ref)
        

class ThisModule(Module):

    def __init__(self, module_name, services):
        super().__init__(module_name)
        self._resource_loader = ResourceLoader(
            services.ref_registry,
            services.type_resolver,
            services.local_type_module_registry,
            services.local_code_module_registry,
            services.resource_registry,
            )
        self._client_resources_dir = services.client_resources_dir

    def init_phase_2(self, services):
        self._resource_loader.load_resources_from_dir(self._client_resources_dir)
