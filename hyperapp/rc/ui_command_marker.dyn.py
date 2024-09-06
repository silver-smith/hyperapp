import inspect

from .code.command_ctr import CommandTemplateCtr
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    is_cls_arg,
    fn_params,
    )


class CommandProbe:

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn, t):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._fn = fn
        self._t = t
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

    def __call__(self, *args, **kw):
        params = fn_params(self._fn)
        param_ofs = 0
        if args and is_cls_arg(self._fn, args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            param_ofs = 1
        ctx_param_count = len(args) - param_ofs + len(kw)
        ctx_params = params[param_ofs:ctx_param_count + param_ofs]
        service_params = params[ctx_param_count + param_ofs:]
        self._add_constructor(self._t, ctx_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _add_constructor(self, t, ctx_params, service_params):
        ctr = CommandTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            ctx_params=ctx_params,
            service_params=service_params,
            )
        self._ctr_collector.add_constructor(ctr)


class CommandWrapper:

    def __init__(self, system, ctr_collector, module_name, service_name, t):
        self._system = system
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._service_name = service_name
        self._t = t

    def __call__(self, fn):
        qual_name = fn.__qualname__.split('.')
        check_not_classmethod(fn)
        check_is_function(fn)
        return CommandProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn, self._t)


def ui_command_marker(t, module_name, system, ctr_collector):
    return CommandWrapper(system, ctr_collector, module_name, 'ui_command', t)


def ui_model_command_marker(t, module_name):
    def _ui_command_wrapper(fn):
        return fn
    return _ui_command_wrapper
