# meta type is type for storing types themselves as data

from .htypes import (
    BUILTIN_MODULE_NAME,
    Type,
    tNone,
    tString,
    tBinary,
    tInt,
    tBool,
    tDateTime,
    TOptional,
    TList,
    )
from .record import TRecord
from .exception import TException
from .hyper_ref import ref_t


builtin_mt = TRecord(BUILTIN_MODULE_NAME, 'builtin_mt', {
    'name': tString,
    })


# Produced by type module parsed, removed by loader.
name_mt = TRecord(BUILTIN_MODULE_NAME, 'name_mt', {
    'name': tString,
    })


optional_mt = TRecord(BUILTIN_MODULE_NAME, 'optional_mt', {
    'base': ref_t,
    })


def optional_from_piece(piece, pyobj_creg):
    base_t = pyobj_creg.invite(piece.base)
    return TOptional(base_t)


list_mt = TRecord(BUILTIN_MODULE_NAME, 'list_mt', {
    'element': ref_t,
    })


def list_from_piece(piece, pyobj_creg):
    element_t = pyobj_creg.invite(piece.element)
    return TList(element_t)


field_mt = TRecord(BUILTIN_MODULE_NAME, 'field_mt', {
    'name': tString,
    'type': ref_t,
    })

record_mt = TRecord(BUILTIN_MODULE_NAME, 'record_mt', {
    'module_name': tString,
    'name': tString,
    'base': TOptional(ref_t),
    'fields': TList(field_mt),
    })

exception_mt = TRecord(BUILTIN_MODULE_NAME, 'exception_mt', {
    'module_name': tString,
    'name': tString,
    'base': TOptional(ref_t),
    'fields': TList(field_mt),
    })


def _field_from_piece(piece, pyobj_creg):
    t = pyobj_creg.invite(piece.type)
    return (piece.name, t)


def _field_dict_from_piece_list(field_list, pyobj_creg):
    return dict(_field_from_piece(field, pyobj_creg) for field in field_list)


def record_from_piece(piece, pyobj_creg):
    if piece.base is not None:
        base_t = pyobj_creg.invite(piece.base)
        assert isinstance(base_t, TRecord), f"Record base is not a record: {base_t}"
    else:
        base_t = None
    field_dict = _field_dict_from_piece_list(piece.fields, pyobj_creg)
    return TRecord(piece.module_name, piece.name, field_dict, base=base_t)


def exception_from_piece(piece, pyobj_creg):
    if piece.base is not None:
        base_t = pyobj_creg.invite(piece.base)
        assert isinstance(base_t, TException), f"Exception base is not an exception: {base_t}"
    else:
        base_t = None
    field_dict = _field_dict_from_piece_list(piece.fields, pyobj_creg)
    return TException(piece.module_name, piece.name, field_dict, base=base_t)



def register_builtin_meta_types(builtin_types, pyobj_creg):
    builtin_types.register(pyobj_creg, name_mt)
    builtin_types.register(pyobj_creg, optional_mt)
    builtin_types.register(pyobj_creg, list_mt)
    builtin_types.register(pyobj_creg, field_mt)
    builtin_types.register(pyobj_creg, record_mt)
    builtin_types.register(pyobj_creg, exception_mt)


def register_meta_types(pyobj_creg):
    # name_mt does not produce a type, it is removed by type module loader.
    pyobj_creg.register_actor(optional_mt, optional_from_piece, pyobj_creg)
    pyobj_creg.register_actor(list_mt, list_from_piece, pyobj_creg)
    pyobj_creg.register_actor(record_mt, record_from_piece, pyobj_creg)
    pyobj_creg.register_actor(exception_mt, exception_from_piece, pyobj_creg)
