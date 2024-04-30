from hyperapp.common.association_registry import Association

from . import htypes
from .services import (
    constructor_creg,
    data_to_res,
    mosaic,
    pyobj_creg,
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


def _make_d_instance_res(t):
    t_res = pyobj_creg.reverse_resolve(t)
    return htypes.builtin.call(
        function=mosaic.put(t_res),
        )


def _make_command(piece, custom_types, module_res, attr, command_t, d):
    attribute = htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )
    command = command_t(
        d=tuple(mosaic.put(d_piece) for d_piece in d),
        name=piece.name,
        function=mosaic.put(attribute),
        params=piece.params,
        )
    return (attribute, command)


@constructor_creg.actor(htypes.rc_constructors.ui_command_ctr)
def construct_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, ui_command = _make_command(
        piece, custom_types, module_res, attr, htypes.ui.ui_command, (command_d_res,))
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=ui_command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.ui_command'] = ui_command
    return [association]


@constructor_creg.actor(htypes.rc_constructors.ui_model_command_ctr)
def construct_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    model_command_kind_d_res = _make_d_instance_res(htypes.ui.model_command_kind_d)
    attribute, model_command = _make_command(
        piece, custom_types, module_res, attr, htypes.ui.model_command, (command_d_res, model_command_kind_d_res))
    ui_command = htypes.ui.ui_model_command(
        d=(
            mosaic.put(command_d_res),
            ),
        name=piece.name,
        model_command=mosaic.put(model_command),
        )
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=ui_command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res['model_command_kind_d'] = model_command_kind_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.model_command'] = model_command
    name_to_res[f'{attr.name}.ui_command'] = ui_command
    return [association]


@constructor_creg.actor(htypes.rc_constructors.universal_ui_command_ctr)
def construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, ui_command = _make_command(
        piece, custom_types, module_res, attr, htypes.ui.ui_command, (command_d_res,))
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=ui_command,
        )
    name_to_res['universal_ui_command_d'] = dir_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.universal_ui_command'] = ui_command
    return [association]


@constructor_creg.actor(htypes.rc_constructors.universal_ui_model_command_ctr)
def construct_universal_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    model_command_kind_d_res = _make_d_instance_res(htypes.ui.model_command_kind_d)
    attribute, model_command = _make_command(
        piece, custom_types, module_res, attr, htypes.ui.model_command, (command_d_res, model_command_kind_d_res))
    ui_command = htypes.ui.ui_model_command(
        d=(
            mosaic.put(command_d_res),
            ),
        name=piece.name,
        model_command=mosaic.put(model_command),
        )
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=ui_command,
        )
    name_to_res['universal_ui_command_d'] = dir_res
    name_to_res['model_command_kind_d'] = model_command_kind_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.model_command'] = model_command
    name_to_res[f'{attr.name}.universal_ui_command'] = ui_command
    return [association]
