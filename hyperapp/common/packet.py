from .htypes import tBinary, Field, TRecord, TList, tRoute
from .interface.code_repository import tModule, tRequirement


tServerRoute = TRecord([
    Field('public_key_der', tBinary),
    Field('routes', TList(tRoute)),
    ])

tAuxInfo = TRecord([
    Field('requirements', TList(tRequirement)),
    Field('modules', TList(tModule)),
    Field('routes', TList(tServerRoute)),
    ])

tPacket = TRecord([
    Field('aux_info', tAuxInfo),
    Field('payload', tBinary),
    ])
