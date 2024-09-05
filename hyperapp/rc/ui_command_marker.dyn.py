import inspect

from .code.command_ctr import CommandTemplateCtr


def _check_is_function(fn):
    if not inspect.isfunction(fn):
        raise RuntimeError(
            f"Unknown object attempted to be marked as an actor: {fn!r};"
            " Expected function, classmethod or staticmethod"
            )


def _check_not_classmethod(fn):
    if type(fn) is classmethod:
        raise RuntimeError(
            f"Wrap this method first with marker and then with classmethod (classmethod should be first): {fn!r}"
            )

    
def _is_cls_arg(fn, arg):
    # Check arg is a class (MyClass).
    if not isinstance(arg, type):
        return False
    # Resolve MyClass.my_function attribute.
    attr = getattr(arg, fn.__name__, None)
    if attr is None:
        return False
    # Check if class MyClass.my_function is bound to is arg.
    return getattr(attr, '__self__', None) is arg


def _fn_params(fn):
    return list(inspect.signature(fn).parameters)


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
        params = _fn_params(self._fn)
        param_ofs = 0
        if args and _is_cls_arg(self._fn, args[0]):
            # self._fn is a classmethod and args[0] is a 'cls' argument.
            param_ofs = 1
        creg_param_count = len(args) - param_ofs + len(kw)
        creg_params = params[param_ofs:creg_param_count + param_ofs]
        service_params = params[creg_param_count + param_ofs:]
        self._add_constructor(self._t, creg_params, service_params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        return self._fn(*args, **kw, **service_kw)

    def _add_constructor(self, t, creg_params, service_params):
        ctr = CommandTemplateCtr(
            module_name=self._module_name,
            attr_qual_name=self._fn.__qualname__.split('.'),
            service_name=self._service_name,
            t=t,
            creg_params=creg_params,
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
        _check_not_classmethod(fn)
        _check_is_function(fn)
        return CommandProbe(self._system, self._ctr_collector, self._module_name, self._service_name, fn, self._t)


def ui_command_marker(t, module_name, system, ctr_collector):
    return CommandWrapper(system, ctr_collector, module_name, 'ui_command', t)


def ui_model_command_marker(t, module_name):
    def _ui_command_wrapper(fn):
        return fn
    return _ui_command_wrapper
