from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor
from .code.d_type import d_type


STATE_PARAMS = {'state', 'model_state', 'current_item', 'current_idx', 'current_key', 'current_path'}
LOCAL_PARAMS = {'controller', 'ctx', 'lcs', 'rpc_endpoint', 'identity', 'remote_peer'}


def _is_state_param(name):
    return name in STATE_PARAMS or name.startswith('current_')


class CommandTemplateCtr(Constructor):

    def __init__(self, module_name, attr_qual_name, service_name, enum_service_name, ctx_params, service_params, args):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._enum_service_name = enum_service_name
        self._ctx_params = ctx_params
        self._service_params = service_params
        self._args = args

    @property
    def _have_args(self):
        return bool(self._args)

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
        if self._have_args:
            service_name = self._enum_service_name
            if not service_name:
                attr_path = ".".join(self._attr_qual_name)
                raise RuntimeError(
                    f"Command arguments are not supported for {self._service_name} commands:"
                    f" {self._module_name}:{attr_path}")
        else:
            service_name = self._service_name
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        # ready target may already have provider set, but in case of
        # non-typed marker it have not.
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            service_name, self._resource_name,
            provider=resource_tgt,
            ctr=self,
            )
        # resource target may already have resolved target, but in case of
        # non-typed marker it have not.
        resource_tgt.add_cfg_item_target(resolved_tgt)

    @property
    def _fn_name(self):
        return '_'.join(self._attr_qual_name)

    def _command_d(self, types, name):
        code_name = self._module_name.split('.')[-1]
        d_t = d_type(types, code_name, name)
        return d_t()

    def _make_args_picker_command_enum(self, types, name, commit_fn, name_to_res):
        commit_d = self._command_d(types, name)
        open_d = htypes.command.open_args_picker_command_d(
            commit_command_d=mosaic.put(commit_d),
            )
        required_args = tuple(
            htypes.command.arg_t(
                name=name,
                t=pyobj_creg.actor_to_ref(t),
                )
            for name, t in self._args.items()
            )
        command_enum = self._enum_command_t(
            name=name,
            is_global=self._is_global,
            required_args=required_args,
            args_picker_command_d=mosaic.put(open_d),
            commit_command_d=mosaic.put(commit_d),
            commit_fn=mosaic.put(commit_fn),
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.commit-d'] = commit_d
            name_to_res[f'{self._fn_name}.open-d'] = open_d
            name_to_res[f'{self._fn_name}.commit-fn'] = commit_fn
        return command_enum

    def _make_command(self, types, name, fn, name_to_res):
        d = self._command_d(types, name)
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=any(_is_state_param(name) for name in self._ctx_params),
            remotable=not set(self._ctx_params) & LOCAL_PARAMS,
            )
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.d'] = d
            name_to_res[f'{self._fn_name}.fn'] = fn
        return self._command_t(
            d=mosaic.put(d),
            properties=properties,
            system_fn=mosaic.put(fn),
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
        fn = htypes.system_fn.ctx_fn(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        name = self._attr_qual_name[-1]
        if self._have_args:
            command = self._make_args_picker_command_enum(types, name, fn, name_to_res)
        else:
            command = self._make_command(types, name, fn, name_to_res)
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.{self._command_resource_suffix}'] = command
        return command

    @property
    def _command_resource_suffix(self):
        if self._have_args:
            return self._command_enum_resource_suffix
        else:
            return self._direct_command_resource_suffix


class UntypedCommandTemplateCtr(CommandTemplateCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            enum_service_name=piece.enum_service_name,
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
            enum_service_name=self._enum_service_name,
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
            enum_service_name=piece.enum_service_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            args=cls._args_dict(piece.args),
            t=pyobj_creg.invite(piece.t),
            )

    def __init__(self, module_name, attr_qual_name, service_name, enum_service_name, ctx_params, service_params, args, t):
        super().__init__(module_name, attr_qual_name, service_name, enum_service_name, ctx_params, service_params, args)
        self._t = t

    @property
    def piece(self):
        return self._template_ctr_t(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            enum_service_name=self._enum_service_name,
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
    _enum_command_t = htypes.command.ui_args_picker_command_enumerator
    _template_ctr_t = htypes.command_resource.ui_command_template_ctr
    _is_global = False
    _direct_command_resource_suffix = 'ui-command'
    _command_enum_resource_suffix = 'ui-command-enumerator'


class UniversalUiCommandTemplateCtr(UntypedCommandTemplateCtr):

    _command_t = htypes.command.ui_command
    _enum_command_t = htypes.command.ui_args_picker_command_enumerator
    _template_ctr_t = htypes.command_resource.universal_ui_command_template_ctr
    _is_global = False
    _direct_command_resource_suffix = 'universal-ui-command'
    _command_enum_resource_suffix = 'universal-ui-command-enumerator'


class UiCommandEnumeratorTemplateCtr(TypedCommandTemplateCtr):

    _template_ctr_t = htypes.command_resource.ui_command_enumerator_template_ctr
    _is_global = False
    _direct_command_resource_suffix = 'ui-command-enumerator'

    def _make_command(self, types, name, fn, name_to_res):
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.fn'] = fn
        return htypes.command.ui_command_enumerator(
            system_fn=mosaic.put(fn),
            )


class ModelCommandTemplateCtr(TypedCommandTemplateCtr):

    _command_t = htypes.command.model_command
    _enum_command_t = htypes.command.model_args_picker_command_enumerator
    _template_ctr_t = htypes.command_resource.model_command_template_ctr
    _is_global = False
    _direct_command_resource_suffix = 'model-command'
    _command_enum_resource_suffix = 'model-command-enumerator'


class ModelCommandEnumeratorTemplateCtr(TypedCommandTemplateCtr):

    _template_ctr_t = htypes.command_resource.model_command_enumerator_template_ctr
    _is_global = False
    _direct_command_resource_suffix = 'model-command-enumerator'

    def _make_command(self, types, name, fn, name_to_res):
        if name_to_res is not None:
            name_to_res[f'{self._fn_name}.fn'] = fn
        return htypes.command.model_command_enumerator(
            system_fn=mosaic.put(fn),
            )


class GlobalModelCommandTemplateCtr(UntypedCommandTemplateCtr):

    _command_t = htypes.command.model_command
    _template_ctr_t = htypes.command_resource.global_model_command_template_ctr
    _is_global = True
    _direct_command_resource_suffix = 'global-model-command'
