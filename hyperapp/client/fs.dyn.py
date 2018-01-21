import logging

from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.interface import core as core_types
from ..common.interface import fs as fs_types
from ..common.list_object import Element, Chunk
from .command import command
from .referred_registry import ReferredRegistry, ReferredResolver
from .module import Module
from .list_object import ListObject

log = logging.getLogger(__name__)


class FsDirObject(ListObject):

    objimpl_id = 'fs_dir'

    @classmethod
    async def from_state(cls, state, ref_registry, handle_resolver, fs_service_resolver):
        fs_service = await fs_service_resolver.resolve(state.fs_service_ref)
        return cls(ref_registry, handle_resolver, fs_service, state.host, state.path)

    def __init__(self, ref_registry, handle_resolver, fs_service, host, path):
        ListObject.__init__(self)
        self._ref_registry = ref_registry
        self._handle_resolver = handle_resolver
        self._fs_service = fs_service
        self._host = host
        self._path = path
        self._key2row = {}  # cache for visited rows

    def get_state(self):
        return fs_types.fs_dir_object(self.objimpl_id, self._fs_service.to_ref(), self._host, self._path)

    def get_title(self):
        return '%s:/%s' % (self._host, '/'.join(self._path))

    def get_command_list(self, kinds):
        command_list = ListObject.get_command_list(self, kinds)
        if not self._path:
            return [command for command in command_list if command.id != 'open_parent']
        else:
            return command_list

    def pick_current_refs(self):
        return [self._get_path_ref(self._path)]

    def get_columns(self):
        return [
            Column('key', is_key=True),
            Column('ftype'),
            Column('ftime', type=tInt),
            Column('fsize', type=tInt),
            ]

    def get_key_column_id(self):
        return 'key'

    async def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        chunk = await self._fs_service.fetch_dir_contents(
            self._host, self._path, sort_column_id, from_key, desc_count, asc_count)
        self._key2row.update({row.key: row for row in chunk.rows})
        elements = [Element(row.key, row, commands=None, order_key=getattr(row, sort_column_id))
                    for row in chunk.rows]
        list_chunk = Chunk(sort_column_id, from_key, elements, chunk.bof, chunk.eof)
        self._notify_fetch_result(list_chunk)
        return list_chunk

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- FsDirObject.process_diff self=%r diff=%r', id(self), diff)

    def get_element_command_list(self, element_key):
        all_command_list = ListObject.get_element_command_list(self, element_key)
        row = self._key2row[element_key]
        if row.ftype == 'dir':
            return all_command_list
        else:
            return [command for command in all_command_list if command.id != 'open']

    def _get_path_ref(self, path):
        fs_service_ref = self._fs_service.to_ref()
        object = fs_types.fs_ref(fs_service_ref, self._host, path)
        return self._ref_registry.register_new_object(fs_types.fs_ref, object)

    async def _open_path(self, path):
        ref = self._get_path_ref(path)
        return (await self._handle_resolver.resolve(ref))

    @command('open', kind='element')
    async def command_open(self, element_key):
        path = self._path + [element_key]
        return (await self._open_path(path))

    @command('open_parent')
    async def command_open_parent(self):
        if len(self._path) > 0:
            path = self._path[:-1]
            return (await self._open_path(path))


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        services.fs_service_registry = fs_service_registry = ReferredRegistry('fs_service', services.type_registry_registry)
        services.fs_service_resolver = fs_service_resolver = ReferredResolver(services.ref_resolver, fs_service_registry)
        services.handle_registry.register(fs_types.fs_ref, self.resolve_fs_object)
        services.objimpl_registry.register(
            FsDirObject.objimpl_id, FsDirObject.from_state, services.ref_registry, services.handle_resolver, fs_service_resolver)

    async def resolve_fs_object(self, fs_object):
        dir_object = fs_types.fs_dir_object(FsDirObject.objimpl_id, fs_object.fs_service_ref, fs_object.host, fs_object.path)
        handle_t = list_handle_type(core_types, tString)
        sort_column_id = 'key'
        resource_id = ['client_module', 'fs', 'FsDirObject']
        return handle_t('list', dir_object, resource_id, sort_column_id, key=None)
