# load&save client application state from/to file

import os.path
import logging
from ..common.util import encode_path, decode_path, flatten
from ..common.htypes import TList, TRecord, Field, tString
from ..common.requirements_collector import RequirementsCollector
from ..common.visual_rep import pprint
from ..common.packet_coders import packet_coders
from . import window

log = logging.getLogger(__name__)


STATE_FILE_PATH = os.path.expanduser('~/.hyperapp.state.json')
STATE_REQUIREMENTS_FILE_PATH = os.path.expanduser('~/.hyperapp.state.requirements.json')
STATE_FILE_ENCODING = 'json_pretty'


class ApplicationStateStorage(object):

    def __init__(self, packet_types, resource_types, core_types, param_editor_types,
                 objimpl_registry, view_registry, param_editor_registry, type_module_repository, resources_manager, module_manager, code_repository):
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
        self._code_repository = code_repository
        self._state_requirements_type = TRecord([
            Field('module_ids', TList(tString)),
            Field('code_modules', TList(packet_types.module)),
            Field('resource_rec_list', resource_types.resource_rec_list),
            ])
        self._state_type = TList(window.get_state_type())
        
    def save_state(self, state):
        collector = RequirementsCollector(self._core_types, self._param_editor_types)
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
        with open(STATE_REQUIREMENTS_FILE_PATH, 'wb') as f:
            state_requirements = self._state_requirements_type(module_ids, code_modules, resources)
            f.write(packet_coders.encode(STATE_FILE_ENCODING, state_requirements, self._state_requirements_type))
        with open(STATE_FILE_PATH, 'wb') as f:
            f.write(packet_coders.encode(STATE_FILE_ENCODING, state, self._state_type))

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
        state_requirements = self._load_state_file(self._state_requirements_type, STATE_REQUIREMENTS_FILE_PATH)
        if not state_requirements:
            return None
        log.info('-->8 -- loaded state requirements  ------')
        pprint(self._state_requirements_type, state_requirements)
        log.info('--- 8<------------------------')
        log.info('-- code_modules loaded from state: ids=%r, code_modules=%r',
                 state_requirements.module_ids, [module.fpath for module in state_requirements.code_modules])
        log.info('-- resources loaded from state: %s', ', '.join(encode_path(rec.id) for rec in state_requirements.resource_rec_list))
        type_module_list, new_code_modules, modules_resources = async_loop.run_until_complete(
            self._code_repository.get_modules_by_ids(
                [module_id for module_id in set(state_requirements.module_ids) if not self._module_manager.has_module(module_id)]))
        code_modules = state_requirements.code_modules
        if new_code_modules is not None:  # has code repositories?
            code_modules = new_code_modules   # use new versions
        self._type_module_repository.add_all_type_modules(type_module_list or [])
        self._module_manager.load_code_module_list(code_modules)
        self._resources_manager.register(state_requirements.resource_rec_list + (modules_resources or []))
        return self._load_state_file(self._state_type, STATE_FILE_PATH)

    def _load_state_file(self, t, path):
        try:
            with open(path, 'rb') as f:
                state_data = f.read()
            return packet_coders.decode(STATE_FILE_ENCODING, state_data, t)
        except (EOFError, IOError, IndexError, UnicodeDecodeError) as x:
            log.info('Error loading %r: %r', path, x)
            return None

    def _load_state_with_requirements(self):
        state_requirements = self._load_state_file(self._state_requirements_type, STATE_REQUIREMENTS_FILE_PATH)
        if not state_requirements:
            return None
        log.info('-->8 -- loaded state requirements  ------')
        pprint(self._state_requirements_type, state_requirements)
        log.info('--- 8<------------------------')
        log.info('-- code_modules loaded from state: ids=%r, code_modules=%r',
                 state_requirements.module_ids, [module.fpath for module in state_requirements.code_modules])
        log.info('-- resources loaded from state: %s', ', '.join(encode_path(rec.id) for rec in state_requirements.resource_rec_list))
        type_module_list, new_code_modules, modules_resources = self._loop.run_until_complete(
            self._code_repository.get_modules_by_ids(
                [module_id for module_id in set(state_requirements.module_ids) if not self._module_manager.has_module(module_id)]))
        code_modules = state_requirements.code_modules
        if new_code_modules is not None:  # has code repositories?
            code_modules = new_code_modules   # use new versions
        self._type_module_repository.add_all_type_modules(type_module_list or [])
        self._module_manager.load_code_module_list(code_modules)
        self._resources_manager.register(state_requirements.resource_rec_list + (modules_resources or []))
        return self._load_state_file(self._state_type, STATE_FILE_PATH)
