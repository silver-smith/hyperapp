import codecs


def _ref_to_str(ref):
    hash_hex = codecs.encode(ref.hash, 'hex').decode()
    return '%s_%s' % (ref.hash_algorithm, hash_hex)


class CodeModuleImporter(object):

    def __init__(self, ref_resolver):
        self._ref_resolver = ref_resolver
        self._import_name_to_code_module = {}

    def add_code_module(self, code_module_ref):
        code_module = self._ref_resolver.resolve_ref_to_object(code_module_ref, 'meta_type.code_module')
        import_name = _ref_to_str(code_module_ref)
        self._import_name_to_code_module[import_name] = code_module
