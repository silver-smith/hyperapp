# packet - container for packets from server: includes server packet, modules and information
# required for it's decoding and handling

from .interface import tString, tBinary, Field, TRecord, TList


tModuleDep = TRecord([
    Field('module_id', tString),
    Field('visible_as', tString),
    ])

tModule = TRecord([
    Field('id', tString),  # 'hyperapp.client.dynamic.name'
    Field('deps', TList(tModuleDep)),
    Field('source', tString),
    Field('fpath', tString),
    ])

tPacketContainer = TRecord([
    Field('modules', TList(tModule)),
    Field('packet', tBinary),
    ])
