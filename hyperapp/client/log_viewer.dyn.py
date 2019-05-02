from collections import namedtuple

from hyperapp.common.htypes import tInt, resource_key_t
from hyperapp.common.logger import JsonFileLogStorageReader, json_storage_session_list
from hyperapp.client.command import command
from hyperapp.client.module import ClientModule
from . import htypes
from .tree_object import Column, TreeObject


MODULE_NAME = 'log_viewer'


_LogEntry = namedtuple('_LogEntry', 'idx name type args')


class SessionLogs(TreeObject):

    impl_id = 'session-logs'

    @classmethod
    def from_state(cls, state):
        return cls(JsonFileLogStorageReader(state.session))

    def __init__(self, storage_reader):
        super().__init__()
        self._storage_reader = storage_reader

    def get_state(self):
        return htypes.log_viewer.log_viewer(self.impl_id, self._storage_reader.session)

    def get_title(self):
        return self._storage_reader.session

    def get_columns(self):
        return [
            Column('idx', type=tInt),
            Column('name'),
            Column('type'),
            Column('args'),
            ]

    async def fetch_items(self, path):
        assert not path
        items = []
        leafs = []
        contexts = {}
        path2items = {}
        for idx, entry in enumerate(self._storage_reader.enumerate_entries()):
            if entry['type'] == 'entry':
                leafs.append(entry)
            if entry['type'] == 'context-enter':
                contexts[tuple(entry['context'])] = entry
            items.append(entry)
        self._distribute_fetch_results(path, [
            self._log_entry(contexts, idx, entry) for idx, entry in enumerate(items)])

    def _log_entry(self, contexts, idx, entry):
        if entry['type'] == 'context-exit':
            name = contexts[tuple(entry['context'])]
        else:
            name = entry['name']
        return _LogEntry(
            idx, name, entry['type'],
            ', '.join('{}={}'.format(key, value) for key, value in entry.items()
                      if key not in {'name', 'type', 'context'}))


class ThisModule(ClientModule):

    def __init__(self, services):
        super().__init__(MODULE_NAME, services)
        services.objimpl_registry.register(SessionLogs.impl_id, SessionLogs.from_state)

    @command('open_last_session')
    async def open_last_session(self):
        session_list = json_storage_session_list()
        object = htypes.log_viewer.log_viewer(SessionLogs.impl_id, session_list[-2])
        resource_key = resource_key_t(__module_ref__, ['SessionLogs'])
        return htypes.tree_view.int_tree_handle('tree', object, resource_key, current_path=None)
