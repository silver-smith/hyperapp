from .iface_types import (
    tString,
    Field,
    TRecord,
    TList,
    )
from .interface import RequestCmd, Interface, register_iface


tRequirement = TList(tString)  # [hierarchy id, class id]


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

ModuleDep = tModuleDep.instantiate


tModule = TRecord([
    Field('id', tString),  # uuid
    Field('package', tString),  # like 'hyperapp.client'
    Field('deps', TList(tModuleDep)),
    Field('satisfies', TList(tRequirement)),
    Field('source', tString),
    Field('fpath', tString),
    ])

Module = tModule.instantiate


code_repository_iface = Interface('code_repository', commands=[
    RequestCmd('get_modules', [Field('module_ids', TList(tString))], [Field('modules', TList(tModule))]),
    RequestCmd('get_required_modules', [Field('requirements', TList(tRequirement))], [Field('modules', TList(tModule))]),
    ])

register_iface(code_repository_iface)
