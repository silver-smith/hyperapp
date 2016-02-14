from .htypes import tBinary, Field, TRecord, TList
from .interface.code_repository import tModule, tRequirement


tAuxInfo = TRecord([
    Field('requirements', TList(tRequirement)),
    Field('modules', TList(tModule)),
    ])

AuxInfo = tAuxInfo.instantiate


tPacket = TRecord([
    Field('aux_info', tAuxInfo),
    Field('payload', tBinary),
    ])

Packet = tPacket.instantiate
