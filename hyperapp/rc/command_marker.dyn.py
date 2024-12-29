from hyperapp.common.htypes import Type

from .services import deduce_t
from .code.command_ctr import (
    UiCommandTemplateCtr,
    UniversalUiCommandTemplateCtr,
    ModelCommandTemplateCtr,
    ModelCommandEnumeratorTemplateCtr,
    GlobalModelCommandTemplateCtr,
    )
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )


def real_fn(fn):
    if isinstance(fn, CommandProbe):
        # Multiple wrappers.
        return fn.real_fn
    else:
        return fn


class CommandProbe:

    def __init__(self, system_probe, ctr_collector, module_name, service_name, fn, t=None):
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

    @property
    def real_fn(self):
        return real_fn(self._fn)

    def __call__(self, *args, **kw):
        params = split_params(self.real_fn, args, kw)
        self.add_constructor(params)
        service_kw = {
            name: self._system.resolve_service(name)
            for name in params.service_names
            }
        return self.real_fn(*args, **kw, **service_kw)

    def add_constructor(self, params):
        self._add_constructor(params)
        if isinstance(self._fn, CommandProbe):  # Multiple wrappers?
            self._fn.add_constructor(params)

    def _deduce_piece_t(self, params, name_list):
        for name in name_list:
            try:
                piece = params.values[name]
                break
            except KeyError:
                pass
        else:
            names_str = " or ".join(name_list)
            self._raise_error(f"{names_str} argument is expected for command function: {list(params.values)}")
        return deduce_t(piece)

    def _common_ctr_kw(self, params):
        return dict(
            module_name=self._module_name,
            attr_qual_name=self.real_fn.__qualname__.split('.'),
            service_name=self._service_name,
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            )

    def _raise_error(self, error_msg):
        raise RuntimeError(f"{self.real_fn}: {error_msg}")


class UiCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        # Only type specialized markers are allowed.
        ctr = UiCommandTemplateCtr(
            t=self._t,
            **self._common_ctr_kw(params),
            )
        self._ctr_collector.add_constructor(ctr)


class UniversalUiCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        ctr = UniversalUiCommandTemplateCtr(
            **self._common_ctr_kw(params),
            )
        self._ctr_collector.add_constructor(ctr)


class ModelCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(params, ['piece', 'model'])
        ctr = ModelCommandTemplateCtr(
            t=t,
            **self._common_ctr_kw(params),
            )
        self._ctr_collector.add_constructor(ctr)


class ModelCommandEnumeratorProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(params, ['piece', 'model'])
        ctr = ModelCommandEnumeratorTemplateCtr(
            t=t,
            **self._common_ctr_kw(params),
            )
        self._ctr_collector.add_constructor(ctr)


class GlobalModelCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        assert not self._t
        ctr = GlobalModelCommandTemplateCtr(
            **self._common_ctr_kw(params),
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
        check_not_classmethod(fn)
        check_is_function(real_fn(fn))
        return self._probe_class(self._system, self._ctr_collector, self._module_name, self._service_name, fn, self._t)


class UiCommandWrapper(CommandWrapper):
    _probe_class = UiCommandProbe


class ModelCommandWrapper(CommandWrapper):
    _probe_class = ModelCommandProbe


class ModelCommandEnumeratorWrapper(CommandWrapper):
    _probe_class = ModelCommandEnumeratorProbe


def ui_command_marker(t, module_name, system, ctr_collector):
    if not isinstance(t, Type):
        raise RuntimeError(f"Use type specialized marker, like '@mark.ui_command(my_type)'")
    service_name = 'view_ui_command_reg'
    return UiCommandWrapper(system, ctr_collector, module_name, service_name, t)


def ui_model_command_marker(t, module_name, system, ctr_collector):
    if not isinstance(t, Type):
        raise RuntimeError(f"Use type specialized marker, like '@mark.ui_model_command(my_type)'")
    service_name = 'view_ui_model_command_reg'
    return UiCommandWrapper(system, ctr_collector, module_name, service_name, t)


def universal_ui_command_marker(fn, module_name, system, ctr_collector):
    if isinstance(fn, Type):
        raise RuntimeError(f"Use non-type specialized marker, like '@mark.universal_ui_command'")
    check_is_function(real_fn(fn))
    service_name = 'universal_ui_command_reg'
    return UniversalUiCommandProbe(system, ctr_collector, module_name, service_name, fn)


def model_command_marker(fn_or_t, module_name, system, ctr_collector):
    service_name = 'model_command_reg'
    if isinstance(fn_or_t, Type):
        # Type-specialized variant (@mark.command(my_type)).
        return ModelCommandWrapper(system, ctr_collector, module_name, service_name, t=fn_or_t)
    else:
        # Not type-specialized variant  (@mark.command).
        check_is_function(real_fn(fn_or_t))
        return ModelCommandProbe(system, ctr_collector, module_name, service_name, fn=fn_or_t)


def model_command_enumerator_marker(fn_or_t, module_name, system, ctr_collector):
    service_name = 'model_command_enumerator_reg'
    if isinstance(fn_or_t, Type):
        # Type-specialized variant (@mark.command_enum(my_type)).
        return ModelCommandEnumeratorWrapper(system, ctr_collector, module_name, service_name, t=fn_or_t)
    else:
        # Not type-specialized variant  (@mark.command_enum).
        check_not_classmethod(fn_or_t)
        check_is_function(real_fn(fn_or_t))
        return ModelCommandEnumeratorProbe(system, ctr_collector, module_name, service_name, fn=fn_or_t)


def global_model_command_marker(fn_or_t, module_name, system, ctr_collector):
    service_name = 'global_model_command_reg'
    if isinstance(fn_or_t, Type):
        raise RuntimeError(f"Global commands can not have type specialization: {fn_or_t!r}")
    else:
        # Not type-specialized variant  (@mark.global_command).
        check_not_classmethod(fn_or_t)
        check_is_function(real_fn(fn_or_t))
        return GlobalModelCommandProbe(system, ctr_collector, module_name, service_name, fn=fn_or_t)
