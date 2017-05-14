import os.path
import logging
import asyncio
from PySide import QtCore, QtGui
from ..common.util import encode_path, decode_path, flatten
from ..common.htypes import TList, TRecord, Field, tString
from ..common.url import UrlWithRoutes
from ..common.visual_rep import pprint
from ..common.requirements_collector import RequirementsCollector
from ..common.packet_coders import packet_coders
from .server import Server
from .command import command
from .proxy_object import execute_get_request
from . import view
from . import window
from . import tab_view
from . import navigator
from .services import Services

log = logging.getLogger(__name__)


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state.json')
STATE_FILE_ENCODING = 'json_pretty'


class Application(QtGui.QApplication, view.View):

    def __init__(self, sys_argv):
        QtGui.QApplication.__init__(self, sys_argv)
        self._constructed = False    # Commander constructor getattr calls attributes not yet ready
        view.View.__init__(self)
        self.services = Services()
        self._core_types = self.services.types.core
        self._packet_types = self.services.types.packet
        self._resource_types = self.services.types.resource
        self._resources_manager = self.services.resources_manager
        self._constructed = True
        self._windows = []
        self._loop = asyncio.get_event_loop()
        self._loop.set_debug(True)

    @property
    def response_mgr(self):
        if not self._constructed: return None
        return self._response_mgr

    def get_state(self):
        return [view.get_state() for view in self._windows]

    @asyncio.coroutine
    def open_windows(self, state):
        for s in state or []:
            yield from window.Window.from_state(s, self, self.services.view_registry, self.services.resources_manager)

    def pick_arg(self, kind):
        return None

    def get_global_commands(self):
        return self._commands

    def window_created(self, view):
        self._windows.append(view)

    def window_closed(self, view):
        state = self.get_state()
        self._windows.remove(view)
        if not self._windows:  # Was it the last window? Then it is time to exit
            self.save_state(state)
            asyncio.async(self.stop_loop())  # call it async to allow all pending tasks to complete

    @asyncio.coroutine
    def stop_loop(self):
        self._loop.stop()

    @command('open_server')
    @asyncio.coroutine
    def open_server(self):
        window = self._windows[0]  # usually first window is the current one
        fpath, ftype = QtGui.QFileDialog.getOpenFileName(
            window.get_widget(), 'Load url', os.getcwd(), 'Server url with routes (*.url)')
        url = UrlWithRoutes.load_from_file(self.services.iface_registry, fpath)
        self.services.remoting.add_routes_from_url(url)
        server = Server.from_public_key(self.services.remoting, url.public_key)
        handle = yield from execute_get_request(self.services.remoting, url)
        assert handle  # url's get command must return a handle
        window.get_current_view().open(handle)

    @command('quit')
    def quit(self):
        ## module.set_shutdown_flag()
        state = self.get_state()
        self.save_state(state)
        self._loop.stop()

    def save_state(self, ui_state):
        collector = RequirementsCollector(self._core_types)
        ui_requirements = collector.collect(self._ui_state_type, ui_state)
        resources1 = self._load_required_resources(ui_requirements)
        resource_requirements = collector.collect(self._resource_types.resource_rec_list, resources1)
        resources2 = self._load_required_resources(resource_requirements)
        resources = resources1 + resources2
        requirements = ui_requirements + resource_requirements
        module_ids = list(self._resolve_module_requirements(requirements))
        code_modules = self.services.module_manager.resolve_ids(module_ids)
        log.info('resource requirements for state: %s', ', '.join(map(encode_path, resource_requirements)))
        for module in code_modules:
            log.info('-- code module is stored to state: %r %r (satisfies %s)', module.id, module.fpath, module.satisfies)
        for rec in resources:
            log.info('-- resource is stored to state: %r %r', encode_path(rec.id), rec.resource)
        state = self._state_type(module_ids, code_modules, resources, ui_state)
        state_data = packet_coders.encode(STATE_FILE_ENCODING, state, self._state_type)
        with open(STATE_FILE_PATH, 'wb') as f:
            f.write(state_data)

    def _load_required_resources(self, requirements):
        return flatten([self._resources_manager.resolve_starting_with(decode_path(id))
                        for registry, id in requirements if registry == 'resources'])

    def _resolve_module_requirements(self, requirements):
        for registry_id, id in requirements:
            if registry_id == 'class':
                module_id = self.services.type_module_repository.get_type_module_id_by_class_id(id)
            elif registry_id == 'interface':
                module_id = self.services.type_module_repository.get_type_module_id_by_interface_id(id)
            else:
                if registry_id == 'object':
                    registry = self.services.objimpl_registry
                elif registry_id == 'handle':
                    registry = self.services.view_registry
                elif registry_id == 'resources':
                    continue
                else:
                    assert False, repr(registry_id)  # unknown registry id
                module_id = registry.get_dynamic_module_id(id)
            log.info('requirement for state %s %r', registry_id, id)
            if module_id is not None:  # None for static module
                log.info('\tprovided by module %s', module_id)
                yield module_id

    @property
    def _ui_state_type(self):
        if not self._constructed: return None
        return TList(window.get_state_type())

    @property
    def _state_type(self):
        if not self._constructed: return None
        return TRecord([
            Field('module_ids', TList(tString)),
            Field('code_modules', TList(self._packet_types.module)),
            Field('resource_rec_list', self._resource_types.resource_rec_list),
            Field('ui_state', self._ui_state_type),
            ])

    ## def load_state_and_modules(self):
    ##     state = self.load_state_file()
    ##     if not state:
    ##         return state
    ##     module_ids, modules, pickled_handles = state
    ##     for module in modules:
    ##         self._module_manager.add_code_module(module)
    ##         print '-- module is loaded from state: %r (satisfies %s)' % (module.id, module.satisfies)
    ##     for module in self._module_manager.resolve_ids(module_ids):
    ##         print 'loading cached module required for state: %r' % module.id
    ##         load_client_module(module)
    ##     return pickler.loads(pickled_handles)

    def load_state_file(self):
        try:
            with open(STATE_FILE_PATH, 'rb') as f:
                state_data = f.read()
            return packet_coders.decode(STATE_FILE_ENCODING, state_data, self._state_type)
        except (EOFError, IOError, IndexError, UnicodeDecodeError) as x:
            log.info('Error loading state: %r', x)
            return None

    def get_default_state(self):
        view_state_t = self.services.modules.text_view.View.get_state_type()
        text_object_state_t = self.services.modules.text_object.TextObject.get_state_type()
        text_handle = view_state_t('text_view', text_object_state_t('text', 'hello'))
        navigator_state = navigator.get_state_type()(
            view_id=navigator.View.view_id,
            history=[navigator.get_item_type()('sample text', text_handle)],
            current_pos=0)
        tabs_state = tab_view.get_state_type()(tabs=[navigator_state], current_tab=0)
        window_state = window.get_state_type()(
            tab_view=tabs_state,
            size=window.this_module.size_type(600, 500),
            pos=window.this_module.point_type(1000, 100))
        return [window_state]

    def process_events_and_repeat(self):
        while self.hasPendingEvents():
            self.processEvents()
            # although this event is documented as deprecated, it is essential for qt objects being destroyed:
            self.processEvents(QtCore.QEventLoop.DeferredDeletion)
        self.sendPostedEvents(None, 0)
        self._loop.call_later(0.01, self.process_events_and_repeat)

    def exec_(self):
        state = self.load_state_file()
        if state:
            log.info('-->8 -- loaded state  ------')
            pprint(self._state_type, state)
            log.info('--- 8<------------------------')
            log.info('-- code_modules loaded from state: ids=%r, code_modules=%r', state.module_ids, [module.fpath for module in state.code_modules])
            log.info('-- resources loaded from state: %s', ', '.join(encode_path(rec.id) for rec in state.resource_rec_list))
            type_modules, new_code_modules, modules_resources = self._loop.run_until_complete(
                self.services.code_repository.get_modules_by_ids(
                    [module_id for module_id in set(state.module_ids) if not self.services.module_manager.has_module(module_id)]))
            code_modules = state.code_modules
            if new_code_modules is not None:  # has code repositories?
                code_modules = new_code_modules   # use new versions
            self.services.type_module_repository.add_all_type_modules(type_modules)
            self.services.module_manager.add_code_modules(code_modules)
            self.services.resources_manager.register(state.resource_rec_list + modules_resources)
            ui_state = state.ui_state
        else:
            ui_state = self.get_default_state()
        self._loop.run_until_complete(self.open_windows(ui_state))
        self._loop.call_soon(self.process_events_and_repeat)
        try:
            self._loop.run_forever()
        finally:
            self._loop.close()
