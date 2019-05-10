from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t, ref_t
from hyperapp.common.logger import RecordKind
from hyperapp.common.logger_json_storage import JsonFileLogStorageReader, json_storage_session_list
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from hyperapp.common.type_repr import type_repr_registry
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .items_object import Column
from .tree_object import TreeObject
from .list_object import ListObject

_log = logging.getLogger(__name__)

MODULE_NAME = 'log_viewer'


SessionLogItem = namedtuple('SessionLogItem', 'idx context name type params')
LogRecordItem = namedtuple('LogRecordItem', 'name value details')



def _value_repr(value):
    try:
        t = deduce_value_type(value)
        repr_fn = type_repr_registry[t]
        return repr_fn(value)
    except (DeduceTypeError, KeyError):
        return repr(value)


class Session:

    @classmethod
    def from_session_id(cls, type_resolver, ref_registry, session_id):
        reader = JsonFileLogStorageReader(type_resolver, ref_registry, session_id)
        return cls(session_id, reader)

    def __init__(self, session_id, reader):
        self.session_id = session_id
        self.path2record = {}
        self.path2item_list = {}
        self._load(reader)

    def _load(self, storage_reader):
        context2path = {(): ()}
        for idx, record in enumerate(storage_reader.enumerate_entries()):
            context = context_path = tuple(record.context)
            if record.kind == RecordKind.ENTER:
                context_path = context[:-1]
                context2path[context] = context2path[context_path] + (idx,)
            if record.kind == RecordKind.EXIT:
                continue
            path = context2path[context_path]
            item = self._record2item(idx, record)
            self.path2record[path + (idx,)] = record
            item_list = self.path2item_list.setdefault(path, [])
            item_list.append(item)
    
    def _record2item(self, idx, record):
        return SessionLogItem(
            idx, '/'.join(map(str, record.context)), record.name, record.kind.name.lower(),
            params=', '.join('{}={}'.format(key, _value_repr(value))
                             for key, value in record.params._asdict().items()
                             if key != 't'))


class SessionCache:

    def __init__(self, type_resolver, ref_registry):
        self._type_resolver = type_resolver
        self._ref_registry = ref_registry
        self._session_id_list = json_storage_session_list()
        self._session_id_to_session = {}

    @property
    def prev_session_id(self):
        return self._session_id_list[-2]

    def get_session(self, session_id):
        try:
            return self._session_id_to_session[session_id]
        except KeyError:
            session = Session.from_session_id(self._type_resolver, self._ref_registry, session_id)
            self._session_id_to_session[session_id] = session
            return session

        
class SessionLogs(TreeObject):

    impl_id = 'session-logs'

    @classmethod
    def from_state(cls, state, session_cache):
        return cls(session_cache.get_session(state.session_id))

    def __init__(self, session):
        super().__init__()
        self._session = session

    def get_state(self):
        return htypes.log_viewer.log_viewer(self.impl_id, self._session.session_id)

    def get_title(self):
        return "log: {}".format(self._session.session_id)

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
        item_list = self._session.path2item_list.get(path, [])
        for item in item_list:
            p = path + (item.idx,)
            if p not in self._session.path2item_list:
                self._distribute_fetch_results(p, [])
        self._distribute_fetch_results(path, item_list)

    @command('open', kind='element')
    async def command_open(self, item_path):
        object = htypes.log_viewer.log_record(LogRecord.impl_id, self._session.session_id, item_path)
        resource_key = resource_key_t(__module_ref__, ['LogRecord'])
        return htypes.core.string_list_handle('list', object, resource_key, key=None)


class LogRecord(ListObject):

    impl_id = 'log_record'

    @classmethod
    def from_state(cls, state, ref_resolver, type_resolver, session_cache):
        return cls(ref_resolver, type_resolver, session_cache, state.session_id, state.item_path)

    def __init__(self, ref_resolver, type_resolver, session_cache, session_id, item_path):
        super().__init__()
        self._ref_resolver = ref_resolver
        self._type_resolver = type_resolver
        self._session_cache = session_cache
        self._session_id = session_id
        self._item_path = item_path

    def get_state(self):
        return htypes.log_viewer.log_record(self.impl_id, self._session_id, self._item_path)

    def get_title(self):
        return "{} {}".format(self._session_id, '/'.join(map(str, self._item_path)))

    def get_columns(self):
        return [
            Column('name', is_key=True),
            Column('value'),
            Column('details'),
            ]

    async def fetch_items(self, from_key):
        session = self._session_cache.get_session(self._session_id)
        record = session.path2record.get(tuple(self._item_path))
        if record:
            self._distribute_fetch_results(
                [self._make_item(name, value) for name, value
                 in record.params._asdict().items() if name != 't'])
        self._distribute_eof()

    def _make_item(self, name, value):
        details = None
        if isinstance(value, ref_t):
            capsule = self._ref_resolver.resolve_ref(value)
            if capsule:
                t = self._type_resolver.resolve(capsule.type_ref)
                details = "{} ({}), encoding {}".format(t.name, _value_repr(capsule.type_ref), capsule.encoding)
        return LogRecordItem(name, _value_repr(value), details)


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        self._session_cache = SessionCache(services.type_resolver, services.ref_registry)
        services.objimpl_registry.register(SessionLogs.impl_id, SessionLogs.from_state, self._session_cache)
        services.objimpl_registry.register(LogRecord.impl_id, LogRecord.from_state, services.ref_resolver, services.type_resolver, self._session_cache)

    @command('open_last_session')
    async def open_last_session(self):
        object = htypes.log_viewer.log_viewer(SessionLogs.impl_id, self._session_cache.prev_session_id)
        resource_key = resource_key_t(__module_ref__, ['SessionLogs'])
        return htypes.tree_view.int_tree_handle('tree', object, resource_key, current_path=None)
