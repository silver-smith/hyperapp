import os.path
import re
import glob
import yaml
import logging
from .dict_decoders import DictDecoder


log = logging.getLogger(__name__)


class ResourcesLoader(object):

    def __init__(self, resource_types, param_editor_types):
        self._resource_types = resource_types
        self._param_editor_types = param_editor_types

    def load_unlocalized_resources_from_dir(self, dir):
        for fpath in glob.glob(os.path.join(dir, '*.resources.yaml')):
            module_name = re.match(r'([^.]+)\.resources\.yaml', os.path.basename(fpath)).group(1)
            log.info('Loading resources from %s', fpath)
            for rec in self._load_resources_from_file(fpath):
                yield self._resource_types.resource_rec([module_name] + rec.id, rec.resource)

    def load_localized_resources_from_dir(self, dir):
        for fpath in glob.glob(os.path.join(dir, '*.resources.*.yaml')):
            module_name, lang = re.match(r'([^.]+)\.resources\.([^.]+)\.yaml', os.path.basename(fpath)).groups()
            log.info('Loading resources for language %r from %s', lang, fpath)
            for rec in self._load_resources_from_file(fpath):
                yield self._resource_types.resource_rec([module_name] + rec.id + [lang], rec.resource)

    def _load_resources_from_file(self, fpath):
        with open(fpath) as f:
            object_items = yaml.load(f)
            for object_id, sections in object_items.items():
                if object_id == 'error_messages':
                    for rec in self._decode_resource_section('error_messages', sections):
                        yield rec
                else:
                    for section_type, item_elements in sections.items():
                        for rec in self._decode_resource_section(section_type, item_elements):
                            yield self._resource_types.resource_rec([object_id] + rec.id, rec.resource)

    def _decode_resource_section(self, section_type, item_elements):
        for item_id, items in item_elements.items():
            if section_type == 'commands':
                resource = self._value2command_resource(items)
                item_type = 'command'
            elif section_type == 'columns':
                resource = self._value2column_resource(items)
                item_type = 'column'
            elif section_type == 'param_editors':
                resource = self._value2param_editor_resource(items)
                item_type = 'param_editor'
            elif section_type == 'error_messages':
                resource = self._value2error_message_resource(items)
                item_type = 'error_message'
            else:
                assert False, 'Unknown resource section type: %r' % section_type
            resource_id = [item_type, item_id]
            yield self._resource_types.resource_rec(resource_id, resource)

    def _value2command_resource(self, value):
        return self._resource_types.command_resource(is_default=value.get('is_default', False),
                                                     text=value.get('text'),
                                                     description=value.get('description') or value.get('text'),
                                                     shortcuts=value.get('shortcuts', []))

    def _value2column_resource(self, value):
        return self._resource_types.column_resource(visible=value.get('visible', True),
                                                    text=value.get('text'),
                                                    description=value.get('description'))

    def _value2param_editor_resource(self, value):
        decoder = DictDecoder()
        param_editor = decoder.decode_dict(self._param_editor_types.param_editor, value)
        return self._param_editor_types.param_editor_resource(param_editor)

    def _value2error_message_resource(self, value):
        return self._resource_types.error_message_resource(message=value)
