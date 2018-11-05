import codecs
import importlib
import importlib.machinery
import logging
import sys

log = logging.getLogger(__name__)


def _ref_to_name(ref):
    hash_hex = codecs.encode(ref.hash[:10], 'hex').decode()
    return '%s_%s' % (ref.hash_algorithm, hash_hex)


class _EmptyLoader(object):

    def exec_module(self, module):
        pass


class _CodeModuleLoader(object):

    def __init__(self, code_module):
        self._code_module = code_module

    def exec_module(self, module):
        log.debug('Executing code module %r', module)
        # using compile allows associate file path with loaded module
        ast = compile(self._code_module.source, self._code_module.file_path, 'exec')
        exec(ast, module.__dict__)


class _HTypeRootLoader(object):

    def __init__(self, code_module):
        self._code_module = code_module

    def exec_module(self, module):
        for import_ in self._code_module.type_import_list:
            importlib.import_module('{}.{}'.format(module.__name__, import_.type_module_name))


class _TypeModuleLoader(object):

    def __init__(self, type_import_list):
        self._type_import_list = type_import_list

    def exec_module(self, module):
        for import_ in self._type_import_list:
            module.__dict__[import_.type_name] = 'todo: value'


class CodeModuleImporter(object):

    IMPORT_PACKAGE = 'hyperapp.dynamic'

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._import_name_to_code_module = {}
        self._htypes_name_to_code_module = {}
        self._type_module_name_to_type_import_list = {}

    def register_meta_hook(self):
        sys.meta_path.append(self)

    def unregister_meta_hook(self):
        sys.meta_path.remove(self)

    def import_code_module(self, code_module_ref):
        code_module = self._ref_resolver.resolve_ref_to_object(code_module_ref, 'meta_type.code_module')
        import_name = '{}.{}'.format(self.IMPORT_PACKAGE, _ref_to_name(code_module_ref))
        self._import_name_to_code_module[import_name] = code_module
        self._htypes_name_to_code_module['{}.htypes'.format(import_name)] = code_module
        for import_ in code_module.type_import_list:
            name = '{}.htypes.{}'.format(import_name, import_.type_module_name)
            self._type_module_name_to_type_import_list.setdefault(name, []).append(import_)
        importlib.import_module(import_name)

    # MetaPathFinder implementation
    def find_spec(self, fullname, path, target=None):
        log.debug('find_spec fullname=%r path=%r target=%r', fullname, path, target)
        if fullname == self.IMPORT_PACKAGE:
            return importlib.machinery.ModuleSpec(fullname, _EmptyLoader(), is_package=True)
        code_module = self._import_name_to_code_module.get(fullname)
        if code_module:
            return importlib.machinery.ModuleSpec(fullname, _CodeModuleLoader(code_module), is_package=True)
        code_module = self._htypes_name_to_code_module.get(fullname)
        if  code_module:
            return importlib.machinery.ModuleSpec(fullname, _HTypeRootLoader(code_module), is_package=True)
        type_import = self._type_module_name_to_type_import_list.get(fullname)
        if type_import:
            return importlib.machinery.ModuleSpec(fullname, _TypeModuleLoader(type_import), is_package=True)
