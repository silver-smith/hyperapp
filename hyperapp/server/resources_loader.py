import os.path
import re
import glob
import yaml
import logging
from ..common.util import encode_path
from ..common.htypes import (
    tString,
    tBool,
    TOptional,
    TList,
    Field,
    TRecord,
    tCommandResource,
    tColumnResource,
    tResourceRec,
    tResourceList,
    )
from ..common.packet_coders import packet_coders

log = logging.getLogger(__name__)


command_rec_t = TRecord([
    Field('is_default', tBool),
    Field('text', tString),
    Field('description', tString),
    Field('shortcuts', TList(tString)),
    ])

column_rec_t = TRecord([
    Field('text', tString),
    Field('description', TOptional(tString)),
    ])

interface_resources_t = TRecord([
    Field('commands', TOptional(TList(command_rec_t))),
    Field('columns', TOptional(TList(column_rec_t))),
    ])


class ResourcesLoader(object):

    def __init__( self, iface_resources_dir, client_modules_resources_dir ):
        self._iface_resources_dir = iface_resources_dir
        self._client_modules_resources_dir = client_modules_resources_dir
        self._resources = []  # tResourceRec list
        self._load_iface_resources()

    def load_resources( self, resource_id ):
        return [rec for rec in self._resources
                if rec.id[:len(resource_id)] == resource_id]
        if resource_id[0] == 'interface':
            return self._iface_resources.get(resource_id[1], [])
        log.warning('### Unknown resource; todo')
        return []  # todo: client module resource loading
        dir = self._dir_map.get(resource_id[0])
        assert dir, 'Unknown resource type: %r' % resource_id[0]
        log.info('loading resources for %r from %r', encode_path(resource_id), dir)
        for fpath in glob.glob(os.path.join(dir, '%s.resources.*.yaml' % resource_id[1])):
            locale = fpath.split('.')[-2]
            log.info('  found resources for locale %r' % locale)
            with open(fpath, 'rb') as f:
                localeResources =  packet_coders.decode('yaml', f.read(), tLocaleResources)
                #yield tResources(resource_id, locale, localeResources)

    def _load_iface_resources( self ):
        for rec in self._load_resources_from_dir(self._iface_resources_dir):
            id = ['interface'] + rec.id[1:]  # skip module name from id
            log.info('    loaded resource %s: %s', encode_path(id), rec.resource)
            self._resources.append(tResourceRec(id, rec.resource))

    def _load_resources_from_dir( self, dir ):
        for fpath in glob.glob(os.path.join(dir, '*.resources.*.yaml')):
            module_name, lang = re.match(r'([^.]+)\.resources\.([^.]+)\.yaml', os.path.basename(fpath)).groups()
            log.info('Loading resources for language %r from %s', lang, fpath)
            with open(fpath) as f:
                iface_items = yaml.load(f)
                for object_id, sections in iface_items.items():
                    return (tResourceRec([module_name, object_id] + rec.id + [lang], rec.resource)
                            for rec in self._decode_resource_sections(sections))

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
