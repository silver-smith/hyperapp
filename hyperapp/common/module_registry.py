import codecs
import importlib
import logging
from collections import defaultdict, namedtuple
from functools import cached_property

from .python_importer import ROOT_PACKAGE, Finder

log = logging.getLogger(__name__)


class _CodeModuleLoader(Finder):

    _is_package = True

    def __init__(self, name, source, file_path):
        self._name = name
        self._source = source
        self._file_path = file_path

    def exec_module(self, module):
        log.debug('Executing code module: %s', self._name)
        # Using compile allows associate file path with loaded module.
        ast = compile(self._source, self._file_path, 'exec')
        # Assign special globals here:
        # module.__dict__['__module_source__'] = self._code_module.source
        # module.__dict__['__module_ref__'] = self._code_module_ref
        exec(ast, module.__dict__)


class _DictLoader(Finder):

    def __init__(self, globals):
        self._globals = globals

    def exec_module(self, module):
        module.__dict__.update(self._globals)


# All .htypes.* modules are loaded automatically, without importing each of them manually.
class _HTypeRootLoader(Finder):

    _is_package = True

    def __init__(self, root_module_name, sub_module_list):
        self._root_module_name = root_module_name
        self._sub_module_list = sub_module_list

    def exec_module(self, module):
        for module_name in self._sub_module_list:
            importlib.import_module(f'{self._root_module_name}.{module_name}')


class CodeModule:

    @classmethod
    def from_piece(cls, code_module, types, web):
        return cls(types, web, code_module)

    def __init__(self, types, web, code_module):
        self._types = types
        self._web = web
        self._code_module = code_module

    @property
    def name(self):
        return self._code_module.module_name
    @property
    def module(self):
        return self._code_module

    # To be used to load all ref (asynchronously) before importing modules.
    @property
    def required_ref_list(self):
        type_ref_list = [
            type_import.type_ref
            for type_import in self._code_module.type_import_list
            ]
        code_ref_list = [
            imp.code_module_ref for imp
            in self._code_module.code_import_list
            ]
        return [*type_ref_list, *code_ref_list]

    @property
    def require_service_list(self):
        return self._code_module.require

    @property
    def provide_service_list(self):
        return self._code_module.provice

    @property
    def used_module_list(self):
        return [module for name, module in self._code_import_list]

    @property
    def root_loader(self):
        return _CodeModuleLoader(
            name=self._code_module.module_name,
            source=self._code_module.source,
            file_path=self._code_module.file_path,
            )

    def get_sub_loader_dict(self, module_to_python_module, module_name):
        return {
            **dict(self._get_type_sub_loader_it(module_name)),
            **dict(self._get_code_sub_loader_dict(module_to_python_module)),
            }

    def init_module(self, services, python_module, config):
        this_module_class = getattr(python_module, 'ThisModule', None)
        if this_module_class:
            log.info("Init module %s (%s) with config: %s", self.name, this_module_class, config)
            this_module = this_module_class(self.name, services, config)
            python_module.__dict__['this_module'] = this_module

    def get_module_method(self, python_module, name):
        this_module = getattr(python_module, 'this_module', None)
        if this_module:
            return getattr(this_module, name, None)
        else:
            return None

    @cached_property
    def _code_import_list(self):
        return [
            (ci.import_name, self._web.summon(ci.code_module_ref)) for ci
            in self._code_module.code_import_list
            ]

    def _get_type_sub_loader_it(self, module_name):
        module_to_globals = defaultdict(dict)
        for type_import in self._code_module.type_import_list:
            t = self._types.resolve(type_import.type_ref)
            module_to_globals[type_import.type_module_name][type_import.type_name] = t
        if not module_to_globals:
            return  # No .htypes module if no types imported.
        yield ('htypes', _HTypeRootLoader(f'{module_name}.htypes', list(module_to_globals)))
        for name, globals in module_to_globals.items():
            sub_name = f'htypes.{name}'
            yield (sub_name, _DictLoader(globals))

    def _get_code_sub_loader_dict(self, module_to_python_module):
        for import_name, module in self._code_import_list:
            python_module = module_to_python_module[module]
            yield (import_name.split('.')[-1], _DictLoader(python_module.__dict__))


class ModuleRegistry:

    _Rec = namedtuple('_Rec', 'name code_module python_module')

    def __init__(self, mosaic, web, python_importer, module_code_registry):
        self._mosaic = mosaic
        self._web = web
        self._python_importer = python_importer
        self._module_code_registry = module_code_registry
        self._registry = {}  # code_module_t -> _Rec

    def import_module_list(self, services, module_list, module_by_requirement, config_dict):
        module_code_list = self._resolve_requirements(module_list, module_by_requirement)
        for module_code in module_code_list:
            config = config_dict.get(module_code.name, {})
            self._import_module(services, module_code, config)

    def enum_method(self, method_name):
        for rec in self._registry.values():
            method = rec.code_module.get_module_method(rec.python_module, method_name)
            if method:
                yield (rec.name, method)

    def get_python_module(self, module):
        return self._registry[module].python_module

    def _resolve_requirements(self, module_list, module_by_requirement):
        seen_set = set()
        wanted_list = list(module_list)
        result_list = []
        while wanted_list:
            module = wanted_list.pop(0)
            seen_set.add(module)
            module_code = self._module_code_registry.animate(module)
            result_list.append(module_code)
            wanted_list += module_code.used_module_list
            for service in module_code.require_service_list:
                provider_set = module_by_requirement[service]
                if not provider_set:
                    raise RuntimeError(f"Code module {module.module_name!r} requires {service!r}, but no module provides it")
                if len(provider_set) > 1:
                    # When requirements is provided by several modules, preferred should be included in module_list.
                    provider_set &= set(module_list)
                [provider] = provider_set  # Only one provider is expected now.
                wanted_list.append(provider)
        return reversed(result_list)
            
    def _import_module(self, services, module_code, config):
        module_name = self._make_module_name(module_code.module)
        module_to_python_module = {
            module: rec.python_module
            for module, rec
            in self._registry.items()
            }
        python_module = self._python_importer.import_module(
            module_name,
            module_code.root_loader,
            module_code.get_sub_loader_dict(module_to_python_module, module_name),
        )
        module_code.init_module(services, python_module, config)
        self._registry[module_code.module] = self._Rec(module_code.name, module_code, python_module)

    def _make_module_name(self, module):
        module_ref = self._mosaic.put(module)
        hash_hex = codecs.encode(module_ref.hash[:10], 'hex').decode()
        return f'{ROOT_PACKAGE}.{module_ref.hash_algorithm}_{hash_hex}'

