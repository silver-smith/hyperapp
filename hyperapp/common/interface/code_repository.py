from ..htypes import (
    tString,
    Field,
    TRecord,
    TList,
    RequestCmd,
    Interface,
    ListInterface,
    Column,
    register_iface,
    )


tRequirement = TList(tString)  # [hierarchy id, class id]


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

tModule = TRecord([
    Field('id', tString),  # uuid
    Field('package', tString),  # like 'hyperapp.client'
    Field('deps', TList(tModuleDep)),
    Field('satisfies', TList(tRequirement)),
    Field('source', tString),
    Field('fpath', tString),
    ])

code_repository_iface = Interface('code_repository', commands=[
    RequestCmd('get_modules_by_ids', [Field('module_ids', TList(tString))], [Field('modules', TList(tModule))]),
    RequestCmd('get_modules_by_requirements', [Field('requirements', TList(tRequirement))], [Field('modules', TList(tModule))]),
    ])

code_repository_browser_iface = ListInterface('code_repository_browser', key_column='id', columns=[
        Column('id', 'Module id'),
        Column('fname', 'File name'),
        Column('package', 'Package'),
        Column('satisfies', 'Satisfies requirements'),
        ])


register_iface(code_repository_iface)
register_iface(code_repository_browser_iface)
