from ..htypes import (
    tString,
    Field,
    TRecord,
    TList,
    tRequirement,
    tModule,
    tResources,
    tTypeModule,
    RequestCmd,
    Interface,
    ListInterface,
    Column,
    register_iface,
    )

code_repository_iface = Interface('code_repository', commands=[
    RequestCmd('get_modules_by_ids',
               [Field('module_ids', TList(tString))],
               [Field('type_modules', TList(tTypeModule)),
                Field('code_modules', TList(tModule)),
                Field('resources', TList(tResources))]),
    RequestCmd('get_modules_by_requirements',
               [Field('requirements', TList(tRequirement))],
               [Field('type_modules', TList(tTypeModule)),
                Field('code_modules', TList(tModule)),
                Field('resources', TList(tResources))]),
    ])

code_repository_browser_iface = ListInterface('code_repository_browser', columns=[
        Column('id', is_key=True),
        Column('fname'),
        Column('package'),
        Column('satisfies'),
        ])


register_iface(code_repository_iface)
register_iface(code_repository_browser_iface)
