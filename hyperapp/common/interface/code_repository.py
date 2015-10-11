from .types import (
    tString,
    Field,
    TRecord,
    TList,
    )
from .interface import RequestCmd, Interface, register_iface


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

ModuleDep = tModuleDep.instantiate


tModule = TRecord([
    Field('id', tString),  # uuid
    Field('package', tString),  # like 'hyperapp.client'
    Field('deps', TList(tModuleDep)),
    Field('source', tString),
    Field('fpath', tString),
    ])

Module = tModule.instantiate


tRequirement = TList(tString)  # [hierarchy id, class id]


code_repository_iface = Interface('code_repository', commands=[
    RequestCmd('get_required_modules', [Field('requirements', TList(tRequirement))], [Field('modules', TList(tModule))]),
    ])

register_iface(code_repository_iface)
