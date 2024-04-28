from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    data_to_res,
    mosaic,
    types,
    web,
  )
from .code.utils import camel_to_snake


def _make_command_d_res(custom_types, module_res, attr):
    d_attr = attr.name + '_d'
    try:
        command_d_ref = custom_types[module_res.module_name][d_attr]
    except KeyError:
        raise RuntimeError(f"Create directory type: {module_res.module_name}.{d_attr}")
    command_d_t = types.resolve(command_d_ref)
    return data_to_res(command_d_t())


def _make_command(piece, custom_types, module_res, attr, command_t):
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    command = command_t(
        d=mosaic.put(command_d_res),
        name=piece.name,
        function=mosaic.put(attribute),
        params=piece.params,
        )
    return (attribute, command_d_res, command)


def _construct_ui_command(piece, custom_types, name_to_res, module_res, attr, command_t):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    attribute, command_d_res, command = _make_command(piece, custom_types, module_res, attr, command_t)
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.ui_command'] = command
    return [association]


@constructor_creg.actor(htypes.rc_constructors.ui_command_ctr)
def construct_ui_command(piece, custom_types, name_to_res, module_res, attr):
    return _construct_ui_command(piece, custom_types, name_to_res, module_res, attr, htypes.ui.ui_command)


@constructor_creg.actor(htypes.rc_constructors.ui_model_command_ctr)
def construct_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    return _construct_ui_command(piece, custom_types, name_to_res, module_res, attr, htypes.ui.ui_model_command)


def _construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr, command_t):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    attribute, command_d_res, command = _make_command(piece, custom_types, module_res, attr, command_t)
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=command,
        )
    name_to_res['universal_ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.universal_ui_command'] = command
    return [association]


@constructor_creg.actor(htypes.rc_constructors.universal_ui_command_ctr)
def construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr):
    return _construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr, htypes.ui.ui_command)


@constructor_creg.actor(htypes.rc_constructors.universal_ui_model_command_ctr)
def construct_universal_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    return _construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr, htypes.ui.ui_model_command)
