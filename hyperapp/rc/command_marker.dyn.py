from hyperapp.boot.htypes import Type

from .services import deduce_t
from .code.command_ctr import (
    UiCommandTemplateCtr,
    UniversalUiCommandTemplateCtr,
    UiCommandEnumeratorTemplateCtr,
    ModelCommandTemplateCtr,
    ModelCommandEnumeratorTemplateCtr,
    GlobalModelCommandTemplateCtr,
    )
from .code.probe import ProbeBase
from .code.marker_utils import (
    check_is_function,
    check_not_classmethod,
    split_params,
    )


class CommandProbe(ProbeBase):

    def __init__(self, system_probe, ctr_collector, module_name, args, fn, t=None):
        super().__init__(system_probe, ctr_collector, module_name, fn)
        self._args = args
        self._t = t
        system_probe.add_global(self)

    def migrate_to(self, system_probe):
        self._system = system_probe
        self._ctr_collector = system_probe.resolve_service('ctr_collector')

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

    def _deduce_view_t(self, params, marker):
        try:
            view = params.values['view']
        except KeyError:
            self._raise_error(f"Use type-specialized variant (@{marker}(my_type)) or add 'view' parameter")
        try:
            piece = view.piece
        except AttributeError:
            self._raise_error(f"View does not have 'piece' property: {view!r}")
        return deduce_t(piece)

    def _common_ctr_kw(self, params):
        args = {
            name: deduce_t(params.values[name])
            for name in self._args or []
            }
        return dict(
            module_name=self._module_name,
            attr_qual_name=params.real_qual_name(self.real_fn),
            ctx_params=params.ctx_names,
            service_params=params.service_names,
            args=args,
            )

    def _raise_error(self, error_msg):
        raise RuntimeError(f"{self.real_fn}: {error_msg}")


class UiCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_view_t(params, 'ui_command')
        if 'element_idx' in params.ctx_names:
            service_name = 'view_element_ui_command_reg'
            enum_service_name = 'view_element_ui_command_enumerator_reg'
        else:
            service_name = 'view_ui_command_reg'
            enum_service_name = 'ui_command_enumerator_reg'
        ctr = UiCommandTemplateCtr(
            **self._common_ctr_kw(params),
            t=t,
            service_name=service_name,
            enum_service_name=enum_service_name,
            )
        self._ctr_collector.add_constructor(ctr)


class UiModelCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_view_t(params, 'ui_command')
        ctr = UiCommandTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='view_ui_model_command_reg',
            enum_service_name=None,
            t=t,
            )
        self._ctr_collector.add_constructor(ctr)


class UniversalUiCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        ctr = UniversalUiCommandTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='universal_ui_command_reg',
            enum_service_name='universal_ui_command_enumerator_reg',
            )
        self._ctr_collector.add_constructor(ctr)


class UiCommandEnumeratorProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_view_t(params, 'ui_command_enum')
        ctr = UiCommandEnumeratorTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='ui_command_enumerator_reg',
            enum_service_name=None,
            t=t,
            )
        self._ctr_collector.add_constructor(ctr)


class ModelCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(params, ['piece', 'model'])
        ctr = ModelCommandTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='model_command_reg',
            enum_service_name='model_command_enumerator_reg',
            t=t,
            )
        self._ctr_collector.add_constructor(ctr)


class ModelCommandEnumeratorProbe(CommandProbe):

    def _add_constructor(self, params):
        if self._t:
            t = self._t
        else:
            t = self._deduce_piece_t(params, ['piece', 'model'])
        ctr = ModelCommandEnumeratorTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='model_command_enumerator_reg',
            enum_service_name=None,
            t=t,
            )
        self._ctr_collector.add_constructor(ctr)


class GlobalModelCommandProbe(CommandProbe):

    def _add_constructor(self, params):
        assert not self._t
        ctr = GlobalModelCommandTemplateCtr(
            **self._common_ctr_kw(params),
            service_name='global_model_command_reg',
            enum_service_name=None,
            )
        self._ctr_collector.add_constructor(ctr)


class CommandDecorator:

    def __init__(self, system, ctr_collector, module_name, args):
        self._system = system
        self._ctr_collector = ctr_collector
        self._module_name = module_name
        self._args = args


class TypedCommandDecorator(CommandDecorator):

    def __init__(self, system, ctr_collector, module_name, args, t):
        super().__init__(system, ctr_collector, module_name, args)
        self._t = t

    def __call__(self, fn):
        check_not_classmethod(fn)
        check_is_function(fn)
        return self._probe_class(self._system, self._ctr_collector, self._module_name, self._args, fn, self._t)


class UntypedCommandDecorator(CommandDecorator):

    def __call__(self, fn):
        if isinstance(fn, Type):
            raise RuntimeError(f"{self._command_desc} commands can not have type specialization: {fn!r}")
        check_not_classmethod(fn)
        check_is_function(fn)
        return self._probe_class(self._system, self._ctr_collector, self._module_name, self._args, fn)


class UiCommandDecorator(TypedCommandDecorator):
    _probe_class = UiCommandProbe


class UiModelCommandDecorator(TypedCommandDecorator):
    _probe_class = UiModelCommandProbe


class UniversalUiCommandDecorator(UntypedCommandDecorator):
    _probe_class = UniversalUiCommandProbe
    _command_desc = "Universal"


class UiCommandEnumeratorDecorator(TypedCommandDecorator):
    _probe_class = UiCommandEnumeratorProbe


class ModelCommandDecorator(TypedCommandDecorator):
    _probe_class = ModelCommandProbe


class ModelCommandEnumeratorDecorator(TypedCommandDecorator):
    _probe_class = ModelCommandEnumeratorProbe


class GlobalModelCommandDecorator(UntypedCommandDecorator):
    _probe_class = GlobalModelCommandProbe
    _command_desc = "Global"


class CommandMarker:

    def __init__(self, module_name, system, ctr_collector):
        self._module_name = module_name
        self._system = system
        self._ctr_collector = ctr_collector


class UiCommandMarker(CommandMarker):

    def __call__(self, fn_or_t=None, *, args=None):
        if isinstance(fn_or_t, Type) or fn_or_t is None:
            return UiCommandDecorator(self._system, self._ctr_collector, self._module_name, args, t=fn_or_t)
        else:
            # Not type-specialized variant  (@mark.ui_command).
            check_not_classmethod(fn_or_t)
            check_is_function(fn_or_t)
            return UiCommandProbe(self._system, self._ctr_collector, self._module_name, args, fn=fn_or_t)


class UiModelCommandMarker(CommandMarker):

    def __call__(self, t):
        if not isinstance(t, Type):
            raise RuntimeError(f"Use type specialized marker, like '@mark.ui_model_command(my_type)'")
        return UiModelCommandDecorator(self._system, self._ctr_collector, self._module_name, args=None, t=t)


class UniversalUiCommandMarker(CommandMarker):

    def __call__(self, fn=None, *, args=None):
        if fn is None:
            return UniversalUiCommandDecorator(self._system, self._ctr_collector, self._module_name, args)
        if args is not None:
            raise RuntimeError(f"Universal UI commands decorator does not support positional arguments")
        if isinstance(fn, Type):
            raise RuntimeError(f"Use non-type specialized marker, like '@mark.universal_ui_command'")
        check_is_function(fn)
        return UniversalUiCommandProbe(self._system, self._ctr_collector, self._module_name, args=None, fn=fn)


class UiCommandEnumeratorMarker(CommandMarker):

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):
            # Type-specialized variant (@mark.ui_command_enum(my_type)).
            return UiCommandEnumeratorDecorator(self._system, self._ctr_collector, self._module_name, args=None, t=fn_or_t)
        else:
            # Not type-specialized variant  (@mark.ui_command_enum).
            check_not_classmethod(fn_or_t)
            check_is_function(fn_or_t)
            return UiCommandEnumeratorProbe(self._system, self._ctr_collector, self._module_name, args=None, fn=fn_or_t)


class ModelCommandMarker(CommandMarker):

    def __call__(self, fn_or_t=None, *, args=None):
        if fn_or_t is None:
            return ModelCommandDecorator(self._system, self._ctr_collector, self._module_name, args, t=fn_or_t)
        if isinstance(fn_or_t, Type):
            # Type-specialized variant (@mark.command(my_type)).
            return ModelCommandDecorator(self._system, self._ctr_collector, self._module_name, args, t=fn_or_t)
        # Not type-specialized variant  (@mark.command).
        check_is_function(fn_or_t)
        return ModelCommandProbe(self._system, self._ctr_collector, self._module_name, args, fn=fn_or_t)


class ModelCommandEnumeratorMarker(CommandMarker):

    def __call__(self, fn_or_t):
        if isinstance(fn_or_t, Type):
            # Type-specialized variant (@mark.command_enum(my_type)).
            return ModelCommandEnumeratorDecorator(self._system, self._ctr_collector, self._module_name, args=None, t=fn_or_t)
        else:
            # Not type-specialized variant  (@mark.command_enum).
            check_not_classmethod(fn_or_t)
            check_is_function(fn_or_t)
            return ModelCommandEnumeratorProbe(self._system, self._ctr_collector, self._module_name, args=None, fn=fn_or_t)


class GlobalModelCommandMarker(CommandMarker):

    def __call__(self, fn=None, *, args=None):
        if fn is None:
            return GlobalModelCommandDecorator(self._system, self._ctr_collector, self._module_name, args)
        if args is not None:
            raise RuntimeError(f"Global commands decorator does not support positional arguments")
        if isinstance(fn, Type):
            raise RuntimeError(f"Global commands can not have type specialization: {fn!r}")
        else:
            # Not type-specialized variant  (@mark.global_command).
            check_not_classmethod(fn)
            check_is_function(fn)
            return GlobalModelCommandProbe(self._system, self._ctr_collector, self._module_name, args=None, fn=fn)
