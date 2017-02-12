from .htypes import (
    tString,
    tBinary,
    Field,
    TRecord,
    TList,
    tServerRoutes,
    )
from .meta_type import tTypeModule
from .resource_type import tResourceList


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

tAuxInfo = TRecord([
    Field('requirements', TList(tRequirement)),
    Field('type_modules', TList(tTypeModule)),
    Field('modules', TList(tModule)),
    Field('routes', TList(tServerRoutes)),
    Field('resources', tResourceList),
    ])

tPacket = TRecord([
    Field('aux_info', tAuxInfo),
    Field('payload', tBinary),
    ])
