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
from .code.command_params import STATE_PARAMS, LOCAL_PARAMS


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


def _make_attribute(module_res, attr):
    return htypes.builtin.attribute(
        object=mosaic.put(module_res),
        attr_name=attr.name,
        )


def _make_impl(piece, attribute, impl_t):
    return impl_t(
        function=mosaic.put(attribute),
        params=piece.params,
        )


def _make_command(impl, d_res):
    return htypes.ui.command(
        d=mosaic.put(d_res),
        impl=mosaic.put(impl),
        )


def _make_ui_command(piece, custom_types, module_res, attr, d_res):
    attribute = _make_attribute(module_res, attr)
    impl = _make_impl(piece, attribute, htypes.ui.ui_command_impl)
    command = _make_command(impl, d_res)
    return (attribute, impl, command)


def _make_model_command(piece, custom_types, module_res, attr, d_res):
    attribute = _make_attribute(module_res, attr)
    model_command_impl = _make_impl(piece, attribute, htypes.ui.model_command_impl)
    impl = htypes.ui.ui_model_command_impl(
        model_command_impl=mosaic.put(model_command_impl),
        )
    command = _make_command(impl, d_res)
    return (attribute, model_command_impl, impl, command)


def _make_properties(impl, is_global=False, uses_state=False, remotable=False):
    command_properties_d_res = _make_d_instance_res(htypes.ui.command_properties_d)
    properties = htypes.ui.command_properties(
        is_global=is_global,
        uses_state=uses_state,
        remotable=remotable,
        )
    association = Association(
        bases=[command_properties_d_res, impl],
        key=[command_properties_d_res, impl],
        value=properties,
        )
    return command_properties_d_res, properties, association


def _make_fn_impl_properties(impl, is_global=False):
    return _make_properties(
        impl, is_global,
        uses_state=bool(set(impl.params) & STATE_PARAMS),
        remotable=not set(impl.params) & LOCAL_PARAMS,
        )


@constructor_creg.actor(htypes.rc_constructors.ui_command_ctr)
def construct_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, impl, command = _make_ui_command(
        piece, custom_types, module_res, attr, command_d_res)
    command_properties_d_res, props, props_association = _make_fn_impl_properties(impl)
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res['command_properties_d'] = command_properties_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.impl'] = impl
    name_to_res[f'{attr.name}.command'] = command
    name_to_res[f'{attr.name}.command_properties'] = props
    return [association, props_association]


@constructor_creg.actor(htypes.rc_constructors.ui_model_command_ctr)
def construct_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.ui_command_d())
    t_res = web.summon(piece.t)
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, model_command_impl, impl, command = _make_model_command(
        piece, custom_types, module_res, attr, command_d_res)
    command_properties_d_res, props, props_association = _make_fn_impl_properties(model_command_impl)
    association = Association(
        bases=[dir_res, t_res],
        key=[dir_res, t_res],
        value=command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res['command_properties_d'] = command_properties_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.model_command_impl'] = model_command_impl
    name_to_res[f'{attr.name}.impl'] = impl
    name_to_res[f'{attr.name}.command'] = command
    name_to_res[f'{attr.name}.command_properties'] = props
    return [association, props_association]


@constructor_creg.actor(htypes.rc_constructors.universal_ui_command_ctr)
def construct_universal_ui_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, impl, command = _make_ui_command(
        piece, custom_types, module_res, attr, command_d_res)
    command_properties_d_res, props, props_association = _make_fn_impl_properties(impl, is_global=True)
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=command,
        )
    name_to_res['universal_ui_command_d'] = dir_res
    name_to_res['command_properties_d'] = command_properties_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.impl'] = impl
    name_to_res[f'{attr.name}.command'] = command
    name_to_res[f'{attr.name}.command_properties'] = props
    return [association, props_association]


@constructor_creg.actor(htypes.rc_constructors.universal_ui_model_command_ctr)
def construct_universal_ui_model_command(piece, custom_types, name_to_res, module_res, attr):
    dir_res = data_to_res(htypes.ui.universal_ui_command_d())
    command_d_res = _make_command_d_res(custom_types, module_res, attr)
    attribute, model_command_impl, impl, command = _make_model_command(
        piece, custom_types, module_res, attr, command_d_res)
    command_properties_d_res, props, props_association = _make_fn_impl_properties(model_command_impl)
    association = Association(
        bases=[dir_res],
        key=[dir_res],
        value=command,
        )
    name_to_res['ui_command_d'] = dir_res
    name_to_res['command_properties_d'] = command_properties_d_res
    name_to_res[attr.name] = attribute
    name_to_res[f'{attr.name}.d'] = command_d_res
    name_to_res[f'{attr.name}.model_command_impl'] = model_command_impl
    name_to_res[f'{attr.name}.impl'] = impl
    name_to_res[f'{attr.name}.command'] = command
    name_to_res[f'{attr.name}.command_properties'] = props
    return [association, props_association]
