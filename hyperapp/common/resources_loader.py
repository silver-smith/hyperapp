import os.path
import re
import glob
import yaml
import logging
from ..common.htypes import (
    tCommandResource,
    tColumnResource,
    tResourceRec,
    )

log = logging.getLogger(__name__)


class ResourcesLoader(object):

    def load_resources_from_dir( self, dir ):
        for fpath in glob.glob(os.path.join(dir, '*.resources.*.yaml')):
            module_name, lang = re.match(r'([^.]+)\.resources\.([^.]+)\.yaml', os.path.basename(fpath)).groups()
            log.info('Loading resources for language %r from %s', lang, fpath)
            with open(fpath) as f:
                object_items = yaml.load(f)
                for object_id, sections in object_items.items():
                    for rec in (tResourceRec([module_name, object_id] + rec.id + [lang], rec.resource)
                                for rec in self._decode_resource_sections(sections)):
                        yield rec

    def _decode_resource_sections( self, sections ):
        for section_type, item_elements in sections.items():
            for item_id, items in item_elements.items():
                if section_type == 'commands':
                    resource = self._dict2command_resource(items)
                    item_type = 'command'
                elif section_type == 'columns':
                    resource = self._dict2column_resource(items)
                    item_type = 'column'
                else:
                    assert False, 'Unknown resource section type: %r' % section_type
                resource_id = [item_type, item_id]
                yield tResourceRec(resource_id, resource)

    def _dict2command_resource( self, d ):
        return tCommandResource(is_default=d.get('is_default', False),
                                text=d.get('text'),
                                description=d.get('description') or d.get('text'),
                                shortcuts=d.get('shortcuts'))

    def _dict2column_resource( self, d ):
        return tColumnResource(text=d.get('text'),
                               description=d.get('description') or d.get('text'))
