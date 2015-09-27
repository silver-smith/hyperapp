# packet - container for packets from server: includes server packet, modules and information
# required for it's decoding and handling

from .interface import tString, tBinary, Field, TRecord, TList


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

ModuleDep = tModuleDep.instantiate


tModule = TRecord([
    Field('id', tString),  # uuid
    Field('deps', TList(tModuleDep)),
    Field('source', tString),
    Field('fpath', tString),
    ])

Module = tModule.instantiate


tPacketContainer = TRecord([
    Field('modules', TList(tModule)),
    Field('packet', tBinary),
    ])

PacketContainer = tPacketContainer.instantiate
