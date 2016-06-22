from .htypes import tBinary, Field, TRecord, TList, tServerRoutes
from .interface.code_repository import tModule, tRequirement


tAuxInfo = TRecord([
    Field('requirements', TList(tRequirement)),
    Field('modules', TList(tModule)),
    Field('routes', TList(tServerRoutes)),
    ])

tPacket = TRecord([
    Field('aux_info', tAuxInfo),
    Field('payload', tBinary),
    ])
