# load&save client application state from/to file

import os.path
import logging
from ..common.util import encode_path, decode_path, flatten
from ..common.htypes import TList, TRecord, Field, tString, tEmbedded, EncodableEmbedded
from ..common.requirements_collector import RequirementsCollector
from ..common.visual_rep import pprint
from ..common.packet_coders import DecodeError, packet_coders
#from .remoting import RequestError
from . import window

log = logging.getLogger(__name__)


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state.json')
STATE_FILE_ENCODING = 'json'


class ApplicationStateStorage(object):

    def __init__(
            self,
            error_types,
            module_types,
            packet_types,
            resource_types,
            core_types,
            param_editor_types,
            objimpl_registry,
            view_registry,
            param_editor_registry,
            type_module_repository,
            resources_manager,
            module_manager,
            #code_repository,
            ):
        self._error_types = error_types
        self._packet_types = packet_types
        self._resource_types = resource_types
        self._core_types = core_types
        self._param_editor_types = param_editor_types
        self._objimpl_registry = objimpl_registry
        self._view_registry = view_registry
        self._param_editor_registry = param_editor_registry
        self._type_module_repository = type_module_repository
        self._module_manager = module_manager
        self._resources_manager = resources_manager
        #self._code_repository = code_repository
        self._state_with_requirements_type = TRecord([
            Field('module_ids', TList(tString)),
            Field('code_modules', TList(module_types.module)),
            Field('resource_rec_list', resource_types.resource_rec_list),
            Field('state', tEmbedded),
            ])
        self._state_type = TList(window.get_state_type())
        
    def save_state(self, state):
        collector = RequirementsCollector(self._error_types, self._packet_types, self._core_types, self._param_editor_types, self._iface_registry)
        ui_requirements = collector.collect(self._state_type, state)
        resources1 = self._load_required_resources(ui_requirements)
        resource_requirements = collector.collect(self._resource_types.resource_rec_list, resources1)
        resources2 = self._load_required_resources(resource_requirements)
        resources = resources1 + resources2
        requirements = ui_requirements + resource_requirements
        module_ids = list(self._resolve_module_requirements(requirements))
        code_modules = self._module_manager.resolve_ids(module_ids)
        log.info('resource requirements for state: %s', ', '.join(map(encode_path, resource_requirements)))
        for module in code_modules:
            log.info('-- code module is stored to state: %r %r (satisfies %s)', module.id, module.fpath, module.satisfies)
        for rec in resources:
            log.info('-- resource is stored to state: %r %r', encode_path(rec.id), rec.resource)
        state_with_requirements = self._state_with_requirements_type(
            module_ids, code_modules, resources, EncodableEmbedded(self._state_type, state))
        with open(STATE_FILE_PATH, 'wb') as f:
            f.write(packet_coders.encode(STATE_FILE_ENCODING, state_with_requirements, self._state_with_requirements_type))

    def _load_required_resources(self, requirements):
        return flatten([self._resources_manager.resolve_starting_with(decode_path(id))
                        for registry, id in requirements if registry == 'resources'])

    def _resolve_module_requirements(self, requirements):
        for registry_id, id in requirements:
            log.info('requirement for state %s %r', registry_id, id)
            if registry_id == 'class':
                module_id = self._type_module_repository.get_type_module_id_by_class_id(id)
            elif registry_id == 'interface':
                module_id = self._type_module_repository.get_type_module_id_by_interface_id(id)
            else:
                if registry_id == 'object':
                    registry = self._objimpl_registry
                elif registry_id == 'handle':
                    registry = self._view_registry
                elif registry_id == 'resources':
                    continue
                elif registry_id == 'param_editor':
                    registry = self._param_editor_registry
                else:
                    assert False, repr(registry_id)  # unknown registry id
                module_id = registry.get_dynamic_module_id(id)
            if module_id is not None:  # None for static module
                log.info('\tprovided by module %s', module_id)
                yield module_id

    def _load_state_file(self, t, path):
        try:
            with open(path, 'rb') as f:
                state_data = f.read()
            return packet_coders.decode(STATE_FILE_ENCODING, state_data, t)
        except (EOFError, IOError, IndexError, UnicodeDecodeError) as x:
            log.info('Error loading %r: %r', path, x)
            return None

    def load_state_with_requirements(self, async_loop):
        state = self._load_state_file(self._state_with_requirements_type, STATE_FILE_PATH)
        if not state:
            return None
        log.info('-->8 -- loaded state with requirements  ------')
        pprint(state)
        log.info('--- 8<------------------------')
        log.info('-- code_modules loaded from state: ids=%r, code_modules=%r',
                 state.module_ids, [module.fpath for module in state.code_modules])
        log.info('-- resources loaded from state: %s', ', '.join(encode_path(rec.id) for rec in state.resource_rec_list))
        code_modules = state.code_modules
        resources = state.resource_rec_list
        try:
            type_module_list, new_code_modules, modules_resources = async_loop.run_until_complete(
                self._code_repository.get_modules_by_ids(
                    [module_id for module_id in set(state.module_ids) if not self._module_manager.has_module(module_id)]))
            if new_code_modules is not None:  # has code repositories?
                code_modules = new_code_modules   # use new versions
            resources += (modules_resources or [])
            self._type_module_repository.add_all_type_modules(type_module_list or [])
        except RequestError as x:
            log.warning('Unable to load latest modules and resources, using cached ones: %s' % x)
        except Exception as x:
            if isinstance(x, self._error_types.server_error):
                log.warning('Unable to load latest modules and resources, using cached ones: %s' % x)
            else:
                raise
        #self._module_manager.load_code_module_list(code_modules)
        self._resources_manager.register(resources)
        try:
            return state.state.decode(self._state_type)
        except DecodeError as x:
            log.info('Error decoding %r: %r', STATE_FILE_PATH, x)
            return None

    def _load_state_file(self, t, path):
        try:
            with open(path, 'rb') as f:
                state_data = f.read()
            return packet_coders.decode(STATE_FILE_ENCODING, state_data, t)
        except (EOFError, IOError, IndexError, UnicodeDecodeError, DecodeError) as x:
            log.info('Error loading %r: %r', path, x)
            return None
