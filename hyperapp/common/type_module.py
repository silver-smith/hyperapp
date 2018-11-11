from .htypes import ref_t


class LocalTypeModule(object):

    def __init__(self):
        self._name2ref = {}  # name -> meta_ref_t

    def register(self, name, ref):
        assert isinstance(ref, ref_t), repr(ref)
        self._name2ref[name] = ref

    def get(self, name):
        return self._name2ref.get(name)

    def __getitem__(self, name):
        return self._name2ref[name]


class LocalTypeModuleRegistry(object):

    def __init__(self):
        self._registry = {}

    def register(self, name, local_type_module):
        assert isinstance(local_type_module, LocalTypeModule), repr(local_type_module)
        self._registry[name] = local_type_module

    def resolve(self, name):
        return self._registry.get(name)

    def __getitem__(self, name):
        return self._registry[name]
