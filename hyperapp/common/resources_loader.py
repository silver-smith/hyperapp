import os.path
import re
import glob
import yaml
import logging
from .dict_decoders import DictDecoder


log = logging.getLogger(__name__)


class ResourcesLoader(object):

    def __init__( self, resource_types, param_editor_types ):
        self._resource_types = resource_types
        self._param_editor_types = param_editor_types

    def load_unlocalized_resources_from_dir( self, dir ):
        for fpath in glob.glob(os.path.join(dir, '*.resources.yaml')):
            module_name = re.match(r'([^.]+)\.resources\.yaml', os.path.basename(fpath)).group(1)
            log.info('Loading resources from %s', fpath)
            for rec in self._load_resources_from_file(fpath):
                yield self._resource_types.resource_rec([module_name] + rec.id, rec.resource)

    def load_localized_resources_from_dir( self, dir ):
        for fpath in glob.glob(os.path.join(dir, '*.resources.*.yaml')):
            module_name, lang = re.match(r'([^.]+)\.resources\.([^.]+)\.yaml', os.path.basename(fpath)).groups()
            log.info('Loading resources for language %r from %s', lang, fpath)
            for rec in self._load_resources_from_file(fpath):
                yield self._resource_types.resource_rec([module_name] + rec.id + [lang], rec.resource)

    def _load_resources_from_file( self, fpath ):
        with open(fpath) as f:
            object_items = yaml.load(f)
            for object_id, sections in object_items.items():
                for rec in self._decode_resource_sections(sections):
                    yield self._resource_types.resource_rec([object_id] + rec.id, rec.resource)

    def _decode_resource_sections( self, sections ):
        for section_type, item_elements in sections.items():
            for item_id, items in item_elements.items():
                if section_type == 'commands':
                    resource = self._dict2command_resource(items)
                    item_type = 'command'
                elif section_type == 'columns':
                    resource = self._dict2column_resource(items)
                    item_type = 'column'
                elif section_type == 'param_editors':
                    resource = self._dict2param_editor_resource(items)
                    item_type = 'param_editor'
                else:
                    assert False, 'Unknown resource section type: %r' % section_type
                resource_id = [item_type, item_id]
                yield self._resource_types.resource_rec(resource_id, resource)

    def _dict2command_resource( self, d ):
        return self._resource_types.command_resource(is_default=d.get('is_default', False),
                                                     text=d.get('text'),
                                                     description=d.get('description') or d.get('text'),
                                                     shortcuts=d.get('shortcuts', []))

    def _dict2column_resource( self, d ):
        return self._resource_types.column_resource(visible=d.get('visible', True),
                                                    text=d.get('text'),
                                                    description=d.get('description'))

    def _dict2param_editor_resource( self, d ):
        decoder = DictDecoder()
        param_editor = decoder.decode_dict(self._param_editor_types.param_editor, d)
        return self._param_editor_types.param_editor_resource(param_editor)
