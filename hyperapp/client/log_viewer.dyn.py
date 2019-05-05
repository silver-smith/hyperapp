from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.common.logger import RecordKind
from hyperapp.common.logger_json_storage import JsonFileLogStorageReader, json_storage_session_list
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from hyperapp.common.type_repr import type_repr_registry
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import Column, TreeObject

_log = logging.getLogger(__name__)

MODULE_NAME = 'log_viewer'


LogRecordItem = namedtuple('LogRecordItem', 'idx context name type params')


class SessionLogs(TreeObject):

    impl_id = 'session-logs'

    @classmethod
    def from_state(cls, state, type_resolver, ref_registry):
        return cls(JsonFileLogStorageReader(type_resolver, ref_registry, state.session))

    def __init__(self, storage_reader):
        super().__init__()
        self._session = storage_reader.session
        self._path2item_list = self._load_session(storage_reader)

    def get_state(self):
        return htypes.log_viewer.log_viewer(self.impl_id, self._session)

    def get_title(self):
        return self._session

    def get_columns(self):
        return [
            Column('idx', type=tInt),
            Column('context'),
            Column('name'),
            Column('type'),
            Column('params'),
            ]

    async def fetch_items(self, path):
        path = tuple(path)
        item_list = self._path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    def _load_session(self, storage_reader):
        path2item_list = {}
        context2path = {(): ()}
        for idx, record in enumerate(storage_reader.enumerate_entries()):
            context = context_path = tuple(record.context)
            if record.kind == RecordKind.ENTER:
                context_path = context[:-1]
                context2path[context] = context2path[context_path] + (idx,)
            if record.kind == RecordKind.EXIT:
                continue
            path = context2path[context_path]
            item_list = path2item_list.setdefault(path, [])
            item_list.append(self._record2item(idx, record))
        return path2item_list
        
    def _record2item(self, idx, record):
        return LogRecordItem(
            idx, '/'.join(map(str, record.context)), record.name, record.kind.name,
            params=', '.join('{}={}'.format(key, self._value_repr(value))
                             for key, value in record.params._asdict().items()
                             if key != 't'))

    def _value_repr(self, value):
        try:
            t = deduce_value_type(value)
            repr_fn = type_repr_registry[t]
            return repr_fn(value)
        except (DeduceTypeError, KeyError):
            pass
        return repr(value)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SessionLogs.impl_id, SessionLogs.from_state, services.type_resolver, services.ref_registry)

    @command('open_last_session')
    async def open_last_session(self):
        session_list = json_storage_session_list()
        object = htypes.log_viewer.log_viewer(SessionLogs.impl_id, session_list[-2])
        resource_key = resource_key_t(__module_ref__, ['SessionLogs'])
        return htypes.tree_view.int_tree_handle('tree', object, resource_key, current_path=None)
