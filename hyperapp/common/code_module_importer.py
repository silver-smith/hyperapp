import codecs
import importlib
import importlib.machinery
import sys


def _ref_to_name(ref):
    hash_hex = codecs.encode(ref.hash[:10], 'hex').decode()
    return '%s_%s' % (ref.hash_algorithm, hash_hex)


class CodeModuleImporter(object):

    IMPORT_PACKAGE = 'hyperapp.dynamic'

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._import_name_to_code_module = {}
        self._htypes_name_set = set()

    def register_meta_hook(self):
        sys.meta_path.append(self)

    def unregister_meta_hook(self):
        sys.meta_path.remove(self)

    def import_code_module(self, code_module_ref):
        code_module = self._ref_resolver.resolve_ref_to_object(code_module_ref, 'meta_type.code_module')
        import_name = '{}.{}'.format(self.IMPORT_PACKAGE, _ref_to_name(code_module_ref))
        self._import_name_to_code_module[import_name] = code_module
        self._htypes_name_set.add('{}.htypes'.format(import_name))
        importlib.import_module(import_name)

    # MetaPathFinder implementation
    def find_spec(self, fullname, path, target=None):
        if (fullname == self.IMPORT_PACKAGE
                or fullname in self._import_name_to_code_module
                or fullname in self._htypes_name_set):
            return importlib.machinery.ModuleSpec(fullname, self, is_package=True)

    # Loader implementation
    def exec_module(self, module):
        if (module.__name__ == self.IMPORT_PACKAGE
                or module.__name__ in self._htypes_name_set):
            return
        code_module = self._import_name_to_code_module[module.__name__]
        ast = compile(code_module.source, code_module.file_path, 'exec')  # using compile allows to associate file path with loaded module
        exec(ast, module.__dict__)
