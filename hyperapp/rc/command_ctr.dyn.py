from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.d_type import d_type


STATE_PARAMS = {'state', 'model_state', 'current_item', 'current_idx', 'current_path'}
LOCAL_PARAMS = {'controller', 'ctx', 'lcs', 'rpc_endpoint', 'identity', 'remote_peer'}


class CommandTemplateCtr(Constructor):

    def __init__(self, module_name, attr_qual_name, service_name, ctx_params, service_params, args):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._args = args

    @property
    def _args_tuple(self):
        return tuple(
            htypes.command_resource.arg(
                name=name,
                t=pyobj_creg.actor_to_ref(t),
                )
            for name, t in self._args.items()
            )

    @staticmethod
    def _args_dict(arg_list):
        return {
            arg.name: pyobj_creg.invite(arg.t)
            for arg in arg_list
            }

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        # ready target may already have provider set, but in case of
        # non-typed marker it have not.
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            self._service_name, self._resource_name,
            provider=resource_tgt,
            ctr=self,
            )
        # resource target may already have resolved target, but in case of
        # non-typed marker it have not.
        resource_tgt.add_cfg_item_target(resolved_tgt)

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    def _make_command(self, types, system_fn, name_to_res):
        d_t = d_type(types, self._module_name.split('.')[-1], name=self._attr_qual_name[-1])
        d = d_t()
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=bool(set(self._ctx_params) & STATE_PARAMS),
            remotable=not set(self._ctx_params) & LOCAL_PARAMS,
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.d'] = d
        return self._command_t(
            d=mosaic.put(d),
            properties=properties,
            system_fn=mosaic.put(system_fn),
            )

    def _make_command_component(self, types, python_module, name_to_res=None):
        object = python_module
        prefix = []
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
            if name_to_res is not None:
                name_to_res['.'.join([*prefix, name])] = object
            prefix.append(name)
        system_fn = htypes.system_fn.ctx_fn(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        command = self._make_command(types, system_fn, name_to_res)
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.system-fn'] = system_fn
            name_to_res[f'{self._fn_name}.{self._command_resource_suffix}'] = command
        return command


class UntypedCommandTemplateCtr(CommandTemplateCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            args=cls._args_dict(piece.args),
            )

    @property
    def piece(self):
        return self._template_ctr_t(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            args=self._args_tuple,
            )

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.{self._command_resource_suffix}']

    def make_component(self, types, python_module, name_to_res=None):
        return self._make_command_component(types, python_module, name_to_res)

    @property
    def _resource_name(self):
        return self._fn_name


class TypedCommandTemplateCtr(CommandTemplateCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            args=cls._args_dict(piece.args),
            t=pyobj_creg.invite(piece.t),
            )

    def __init__(self, module_name, attr_qual_name, service_name, ctx_params, service_params, args, t):
        super().__init__(module_name, attr_qual_name, service_name, ctx_params, service_params, args)
        self._t = t

    @property
    def piece(self):
        return self._template_ctr_t(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            args=self._args_tuple,
            t=pyobj_creg.actor_to_ref(self._t),
            )

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.command-cfg-item']

    def make_component(self, types, python_module, name_to_res=None):
        command = self._make_command_component(types, python_module, name_to_res)
        cfg_item = htypes.command.cfg_item(
            t=pyobj_creg.actor_to_ref(self._t),
            command=mosaic.put(command),
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.command-cfg-item'] = cfg_item
        return cfg_item

    @property
    def _resource_name(self):
        return f'{self._t.module_name}-{self._t.name}-{self._fn_name}'


class UiCommandTemplateCtr(TypedCommandTemplateCtr):

    _command_t = htypes.command.ui_command
    _template_ctr_t = htypes.command_resource.ui_command_template_ctr
    _is_global = False
    _command_resource_suffix = 'ui-command'


class UniversalUiCommandTemplateCtr(UntypedCommandTemplateCtr):

    _command_t = htypes.command.ui_command
    _template_ctr_t = htypes.command_resource.universal_ui_command_template_ctr
    _is_global = False
    _command_resource_suffix = 'universal-ui-command'


class ModelCommandTemplateCtr(TypedCommandTemplateCtr):

    _command_t = htypes.command.model_command
    _template_ctr_t = htypes.command_resource.model_command_template_ctr
    _is_global = False
    _command_resource_suffix = 'model-command'


class ModelCommandEnumeratorTemplateCtr(TypedCommandTemplateCtr):

    _template_ctr_t = htypes.command_resource.model_command_enumerator_template_ctr
    _is_global = False
    _command_resource_suffix = 'model-command-enumerator'

    def _make_command(self, types, system_fn, name_to_res):
        return htypes.command.model_command_enumerator(
            system_fn=mosaic.put(system_fn),
            )


class GlobalModelCommandTemplateCtr(UntypedCommandTemplateCtr):

    _command_t = htypes.command.model_command
    _template_ctr_t = htypes.command_resource.global_model_command_template_ctr
    _is_global = True
    _command_resource_suffix = 'global-model-command'
