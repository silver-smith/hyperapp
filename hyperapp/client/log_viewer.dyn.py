from collections import namedtuple
import logging

from hyperapp.common.htypes import tInt, resource_key_t, ref_t
from hyperapp.common.logger import RecordKind
from hyperapp.common.logger_json_storage import JsonFileLogStorageReader, json_storage_session_list
from hyperapp.common.htypes.deduce_value_type import DeduceTypeError, deduce_value_type
from hyperapp.common.type_repr import type_repr_registry
from hyperapp.client.module import ClientModule

from . import htypes
from .object_command import command
from .column import Column
from .tree_object import TreeObject
from .list_object import ListObject
from . import data_viewer

_log = logging.getLogger(__name__)


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
    def from_session_id(cls, types, mosaic, session_id):
        reader = JsonFileLogStorageReader(types, mosaic, session_id)
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
                             for key, value in record.params._asdict().items()))


class SessionCache:

    def __init__(self, types, mosaic):
        self._types = types
        self._mosaic = mosaic
        self._session_id_list = json_storage_session_list()
        self._session_id_to_session = {}

    @property
    def prev_session_id(self):
        return self._session_id_list[-2]

    def get_session(self, session_id):
        try:
            return self._session_id_to_session[session_id]
        except KeyError:
            session = Session.from_session_id(self._types, self._mosaic, session_id)
            self._session_id_to_session[session_id] = session
            return session

        
class SessionLogs(TreeObject):

    @classmethod
    def from_state(cls, state, mosaic, session_cache):
        session = session_cache.get_session(state.session_id)
        return cls(mosaic, session)

    def __init__(self, mosaic, session):
        super().__init__()
        self._mosaic = mosaic
        self._session = session

    @property
    def title(self):
        return "log: {}".format(self._session.session_id)

    @property
    def data(self):
        return htypes.log_viewer.log_viewer(self._session.session_id)

    @property
    def category_list(self):
        return [
            *super().category_list,
            'session-logs',
            ]

    @property
    def columns(self):
        return [
            Column('idx', type=tInt, is_key=True),
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
        return htypes.log_viewer.log_record(self._session.session_id, item_path)


class LogRecord(ListObject):

    @classmethod
    def from_state(cls, state, web, types, session_cache):
        session = session_cache.get_session(state.session_id)
        record = session.path2record.get(tuple(state.item_path))
        return cls(web, types, state.session_id, state.item_path, record)

    def __init__(self, web, types, session_id, item_path, record):
        super().__init__()
        self._web = web
        self._types = types
        self._session_id = session_id
        self._item_path = item_path
        self._record = record

    @property
    def title(self):
        return "{} {}".format(self._session_id, '/'.join(map(str, self._item_path)))

    @property
    def data(self):
        return htypes.log_viewer.log_record(self._session_id, self._item_path)

    @property
    def columns(self):
        return [
            Column('name', is_key=True),
            Column('value'),
            Column('details'),
            ]

    async def fetch_items(self, from_key):
        if self._record:
            self._distribute_fetch_results(
                [self._make_item(name, value) for name, value
                 in self._record.params._asdict().items()])
        self._distribute_eof()

    def _make_item(self, name, value):
        details = None
        if isinstance(value, ref_t):
            capsule = self._web.pull(value)
            if capsule:
                t = self._types.resolve(capsule.type_ref)
                details = "{} ({}), encoding {}".format(t.name, _value_repr(capsule.type_ref), capsule.encoding)
        return LogRecordItem(name, _value_repr(value), details)

    @command('open', kind='element')
    async def command_open(self, key):
        value = getattr(self._record.params, key)
        if not isinstance(value, ref_t):
            return None
        return htypes.data_viewer.data_viewer(value)


class ThisModule(ClientModule):

    def __init__(self, module_name, services, config):
        super().__init__(module_name, services)
        self._session_cache = SessionCache(services.types, services.mosaic)
        services.object_registry.register_actor(htypes.log_viewer.log_viewer, SessionLogs.from_state, services.mosaic, self._session_cache)
        services.object_registry.register_actor(htypes.log_viewer.log_record, LogRecord.from_state, services.web, services.types, self._session_cache)

    @command('open_last_session')
    async def open_last_session(self):
        return htypes.log_viewer.log_viewer(self._session_cache.prev_session_id)
