import asyncio
from ..common.htypes import tInt, tString, Column, list_handle_type
from ..common.interface import core as core_types
from ..common.interface import ref_list as ref_list_types
from .module import Module
from .list_object import ListObject


class RefListObject(ListObject):

    objimpl_id = 'ref_list'

    @classmethod
    def from_state(cls, state, service_registry):
        fs_service = service_registry.resolve(state.fs_service)
        return cls(fs_service, state.host, state.path)

    def __init__(self, fs_service, host, path):
        ListObject.__init__(self)
        self._fs_service = fs_service
        self._host = host
        self._path = path

    def get_state(self):
        return fs_types.fs_dir_object(self.objimpl_id, self._fs_service.to_data(), self._host, self._path)

    def get_title(self):
        return '%s:%s' % (self._host, '/'.join(self._path))

    def get_commands(self):
        return ListObject.get_commands(self)

    def get_columns(self):
        return [
            Column('key', is_key=True),
            Column('ftype'),
            Column('ftime', type=tInt),
            Column('fsize', type=tInt),
            ]

    def get_key_column_id(self):
        return 'key'

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        chunk = yield from self._fs_service.fetch_dir_contents(
            self._host, self._path, sort_column_id, from_key, desc_count, asc_count)
        elements = [Element(row.key, row, commands=None, order_key=getattr(row, sort_column_id))
                    for row in chunk.rows]
        list_chunk = Chunk(sort_column_id, from_key, elements, chunk.bof, chunk.eof)
        self._notify_fetch_result(list_chunk)
        return list_chunk

    def process_diff(self, diff):
        assert isinstance(diff, ListDiff), repr(diff)
        log.info('-- FsDirObject.process_diff self=%r diff=%r', id(self), diff)


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self._href_resolver = services.href_resolver
        self._service_registry = services.service_registry
        services.href_object_registry.register(ref_list_types.dynamic_ref_list.id, self.resolve_dynamic_ref_list_object)

    @asyncio.coroutine
    def resolve_dynamic_ref_list_object(self, dynamic_ref_list):
        service = yield from self._href_resolver.resolve_service_ref(dynamic_ref_list.ref_list_service)
        object = ref_list_types.ref_list_object(RefListObject.objimpl_id, service, dynamic_ref_list.ref_list_id)
        handle_t = list_handle_type(core_types, tString)
        sort_column_id = 'id'
        resource_id = ['client', 'ref_list']
        return handle_t('list', object, resource_id, sort_column_id, None)
