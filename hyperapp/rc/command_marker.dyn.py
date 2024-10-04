from hyperapp.common.htypes import Type

from .services import deduce_t
from .code.command_ctr import (
    UiCommandTemplateCtr,
    ModelCommandTemplateCtr,
    GlobalModelCommandTemplateCtr,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    is_cls_arg,
    fn_params,
    )


class CommandProbe:

    def __init__(self, system_probe, ctr_collector, data_to_res, module_name, service_name, fn, t=None):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._service_name = service_name
        self._fn = fn
        self._t = t
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')
        self._data_to_res = system_probe.resolve_service('data_to_res')

    def __call__(self, *args, **kw):
        params = fn_params(self._fn)
        param_ofs = 0
        if args and is_cls_arg(self._fn, args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            param_ofs = 1
        ctx_params = [
            *params[param_ofs:len(args)],
            *kw,
            ]
        service_params = [
            name for name in params[param_ofs:]
            if name not in ctx_params
            ]
        self._add_constructor(args, param_ofs, ctx_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _deduce_piece_t(self, args, param_ofs):
        if len(args) < param_ofs + 1:
            raise RuntimeError(f"First parameter expected to be a piece: {self._fn!r}")
        piece = args[param_ofs]
        return deduce_t(piece)


class UiCommandProbe(CommandProbe):

    def _add_constructor(self, args, param_ofs, ctx_params, service_params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(args, param_ofs)
        ctr = UiCommandTemplateCtr(
            self._data_to_res,
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            ctx_params=ctx_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class ModelCommandProbe(CommandProbe):

    def _add_constructor(self, args, param_ofs, ctx_params, service_params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(args, param_ofs)
        ctr = ModelCommandTemplateCtr(
            self._data_to_res,
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            ctx_params=ctx_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class GlobalModelCommandProbe(CommandProbe):

    def _add_constructor(self, args, param_ofs, ctx_params, service_params):
        assert not self._t
        ctr = GlobalModelCommandTemplateCtr(
            self._data_to_res,
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            ctx_params=ctx_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class CommandWrapper:

    def __init__(self, system, ctr_collector, data_to_res, module_name, service_name, t):
        self._system = system
        self._ctr_collector = ctr_collector
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._service_name = service_name
        self._t = t

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return self._probe_class(self._system, self._ctr_collector, self._data_to_res, self._module_name, self._service_name, fn, self._t)


class UiCommandWrapper(CommandWrapper):
    _probe_class = UiCommandProbe


class ModelCommandWrapper(CommandWrapper):
    _probe_class = ModelCommandProbe


def ui_command_marker(t, module_name, system, ctr_collector, data_to_res):
    if not isinstance(t, Type):
        raise RuntimeError(f"Use type specialized marker, like '@mark.ui_command(my_type)'")
    service_name = 'view_ui_command_reg'
    return UiCommandWrapper(system, ctr_collector, data_to_res, module_name, service_name, t)


# TODO or remove.
def ui_model_command_marker(t, module_name):
    def _ui_command_wrapper(fn):
        return fn
    return _ui_command_wrapper


def model_command_marker(fn_or_t, module_name, system, ctr_collector, data_to_res):
    service_name = 'model_command_reg'
    if isinstance(fn_or_t, Type):
        # Type-specialized variant (@mark.command(my_type)).
        return ModelCommandWrapper(system, ctr_collector, data_to_res, module_name, service_name, t=fn_or_t)
    else:
        # Not type-specialized variant  (@mark.command).
        check_not_classmethod(fn_or_t)
        check_is_function(fn_or_t)
        return ModelCommandProbe(system, ctr_collector, data_to_res, module_name, service_name, fn=fn_or_t)


def global_model_command_marker(fn_or_t, module_name, system, ctr_collector, data_to_res):
    service_name = 'global_model_command_reg'
    if isinstance(fn_or_t, Type):
        raise RuntimeError(f"Global commands can not have type specialization: {fn_or_t!r}")
    else:
        # Not type-specialized variant  (@mark.global_command).
        check_not_classmethod(fn_or_t)
        check_is_function(fn_or_t)
        return GlobalModelCommandProbe(system, ctr_collector, data_to_res, module_name, service_name, fn=fn_or_t)
