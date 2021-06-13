import codecs
import importlib
import importlib.machinery
import importlib.util
import logging
import sys
from pathlib import Path

from .code_module import code_module_t


log = logging.getLogger(__name__)


def _ref_to_name(ref):
    hash_hex = codecs.encode(ref.hash[:10], 'hex').decode()
    return '%s_%s' % (ref.hash_algorithm, hash_hex)


class _Finder:

    _is_package = False

    def create_module(self, spec):
        return None  # use default semantics

    def get_spec(self, fullname):
        return importlib.util.spec_from_loader(fullname, self, is_package=self._is_package)

    
class _EmptyLoader(_Finder):

    _is_package = True

    def exec_module(self, module):
        pass


class _CodeModuleLoader(_Finder):

    _is_package = True

    def __init__(self, code_module_ref, code_module):
        self._code_module_ref = code_module_ref
        self._code_module = code_module

    def exec_module(self, module):
        log.debug('Executing code module %r %s', self._code_module_ref, module)
        # using compile allows associate file path with loaded module
        ast = compile(self._code_module.source, self._code_module.file_path, 'exec')
        module.__dict__['__module_source__'] = self._code_module.source
        module.__dict__['__module_ref__'] = self._code_module_ref
        exec(ast, module.__dict__)


class _HTypeRootLoader(_Finder):

    _is_package = True

    def __init__(self, code_module):
        self._code_module = code_module

    def exec_module(self, module):
        for import_ in self._code_module.type_import_list:
            importlib.import_module('{}.{}'.format(module.__name__, import_.type_module_name))


class _TypeModuleLoader(_Finder):

    def __init__(self, types, type_import_list):
        self._types = types
        self._type_import_list = type_import_list

    def exec_module(self, module):
        for type_import in self._type_import_list:
            t = self._types.resolve(type_import.type_ref)
            module.__dict__[type_import.type_name] = t


class _CopyDictLoader(_Finder):

    def __init__(self, source_module_name):
        self._source_module_name = source_module_name

    def exec_module(self, module):
        module.__dict__.update(sys.modules[self._source_module_name].__dict__)


class _MetaPathFinder:

    def __init__(self, fullname_to_loader):
        self._fullname_to_loader = fullname_to_loader

    # MetaPathFinder implementation
    def find_spec(self, fullname, path, target=None):
        log.debug('find_spec fullname=%r path=%r target=%r', fullname, path, target)
        loader = self._fullname_to_loader.get(fullname)
        if loader:
            return loader.get_spec(fullname)


class CodeModuleImporter:

    ROOT_PACKAGE = 'hyperapp.dynamic'

    def __init__(self, mosaic, types):
        self._mosaic = mosaic
        self._types = types
        self._fullname_to_loader = {self.ROOT_PACKAGE: _EmptyLoader()}
        self._meta_path_finder = _MetaPathFinder(self._fullname_to_loader)
        self._imported_module_ref_set = set()
        self._registry = {}

    @property
    def registry(self):
        return self._registry

    def register_meta_hook(self):
        sys.meta_path.append(self._meta_path_finder)

    def unregister_meta_hook(self):
        sys.meta_path.remove(self._meta_path_finder)

    def import_code_module(self, requirement_to_module_ref_set, code_module_ref, preferred_modules):
        code_module = self._mosaic.resolve_ref(code_module_ref, code_module_t).value
        module_name = self._code_module_ref_to_fullname(code_module_ref)
        fullname_to_loader = {}
        # module itself
        fullname_to_loader[module_name] = _CodeModuleLoader(code_module_ref, code_module)
        # .htypes package
        fullname_to_loader['{}.htypes'.format(module_name)] = _HTypeRootLoader(code_module)
        # .htypes.* modules
        import_module_to_type_import_list = {}
        for type_import in code_module.type_import_list:
            import_module_to_type_import_list.setdefault(type_import.type_module_name, []).append(type_import)
        for import_module_name, type_import_list in import_module_to_type_import_list.items():
            name = '{}.htypes.{}'.format(module_name, import_module_name)
            fullname_to_loader[name] = _TypeModuleLoader(self._types, type_import_list)
        for requirement in code_module.require:
            module_ref_set = requirement_to_module_ref_set[requirement]
            if not module_ref_set:
                raise RuntimeError(f"Code module {code_module.module_name!r} requires {requirement!r}, but no module provides it")
            if len(module_ref_set) > 1:
                # When requirements is provided by several modules, preferred should be included in preferred_modules.
                [module_ref] = module_ref_set & preferred_modules
            else:
                [module_ref] = module_ref_set
            if module_ref not in self._imported_module_ref_set:
                log.info("Code module %s provides %r for %s", module_ref, requirement, code_module.module_name)
                self.import_code_module(requirement_to_module_ref_set, module_ref, preferred_modules)
        # .* code module imports
        for code_import in code_module.code_import_list:
            if code_import.code_module_ref not in self._imported_module_ref_set:
                log.info("Code module %r imports %r", code_module.module_name, code_import.code_module_ref)
                self.import_code_module(requirement_to_module_ref_set, code_import.code_module_ref, preferred_modules)
            source_module_name = self._code_module_ref_to_fullname(code_import.code_module_ref)
            import_name = code_import.import_name.split('.')[-1]
            name = '{}.{}'.format(module_name, import_name)
            fullname_to_loader[name] = _CopyDictLoader(source_module_name)
        for fullname in fullname_to_loader:
            try:
                del sys.modules[fullname]  # should reload if already loaded
            except KeyError:
                pass
        self._fullname_to_loader.update(fullname_to_loader)
        # perform actual load
        log.info('Import code module %s: %s', code_module_ref, code_module.module_name)
        module = importlib.import_module(module_name)
        self._imported_module_ref_set.add(code_module_ref)
        self._registry[code_module_ref] = module
        return module


    @classmethod
    def _code_module_ref_to_fullname(cls, code_module_ref):
        return '{}.{}'.format(cls.ROOT_PACKAGE, _ref_to_name(code_module_ref))
