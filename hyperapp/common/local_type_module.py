from .htypes import (
    tString,
    TRecord,
    TList,
    ref_t,
    )


type_import_t = TRecord('type_import', {
    'module_name': tString,
    'name': tString,
    })

type_def_t = TRecord('typedef', {
    'name': tString,
    'type': ref_t,
    })

type_module_t = TRecord('type_module', {
    'module_name': tString,
    'import_list': TList(type_import_t),
    'typedefs': TList(type_def_t),
    })


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

    def items(self):
        return self._name2ref.items()
