from .services import deduce_t
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    is_cls_arg,
    fn_params,
    )


class ModelProbe:

    def __init__(self, system_probe, ctr_collector, module_name, fn):
        self._system = system_probe
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._fn = fn
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
        param_values = {
            params[idx]: arg
            for idx, arg in enumerate(args)
            }
        param_values = {
            **param_values,
            **kw,
            }
        ctx_params = [
            *params[param_ofs:len(args)],
            *kw,
            ]
        service_params = [
            name for name in params[param_ofs:]
            if name not in ctx_params
            ]
        try:
            model = param_values['model']
        except KeyError:
            try:
                model = param_values['piece']
            except KeyError:
                raise RuntimeError(f"'model' or 'piece' argument is expected for model function: {list(param_values)}")
        model_t = deduce_t(model)
        self._add_constructor(model_t, ctx_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _add_constructor(self, model_t, ctx_params, service_params):
        assert 0, (model_t, ctx_params, service_params)


def model_marker(fn, module_name, system, ctr_collector):
    check_not_classmethod(fn)
    check_is_function(fn)
    return ModelProbe(system, ctr_collector, module_name, fn)
