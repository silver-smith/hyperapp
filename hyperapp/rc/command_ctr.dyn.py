from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor


STATE_PARAMS = {'state', 'model_state', 'current_item', 'current_idx', 'current_path'}
LOCAL_PARAMS = {'controller', 'ctx', 'lcs', 'rpc_endpoint', 'identity', 'remote_peer'}


class CommandTemplateCtr(Constructor):

    def __init__(self, data_to_res, module_name, attr_qual_name, service_name, ctx_params, service_params):
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._ctx_params = ctx_params
        self._service_params = service_params

    def update_targets(self, target_set):
        resource_tgt = target_set.factory.python_module_resource_by_module_name(self._module_name)
        # ready target may already have provider set, but in case of
        # non-typed marker it have not.
        ready_tgt = target_set.factory.config_item_ready(self._service_name, self._resource_name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved(self._service_name, self._resource_name)
        resolved_tgt.resolve(self)
        # Should be created to be added to config resource.
        _ = target_set.factory.config_item_complete(self._service_name, self._resource_name)
        # resource target may already have resolved target, but in case of
        # non-typed marker it have not.
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(resolved_tgt)
        target_set.update_deps_for(resource_tgt)

    def _make_command(self, types, system_fn, name_to_res):
        d_name = self._attr_qual_name[-1] + '_d'
        type_module = self._module_name.split('.')[-1]
        d_t_piece = types.get(type_module, d_name)
        assert d_t_piece, (type_module, d_name)  # TODO: Make type if missing.
        d_t = pyobj_creg.animate(d_t_piece)
        d_piece = self._data_to_res(d_t())
        properties = htypes.command.properties(
            is_global=self._is_global,
            uses_state=bool(set(self._ctx_params) & STATE_PARAMS),
            remotable=not set(self._ctx_params) & LOCAL_PARAMS,
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.d'] = d_piece
        return self._command_t(
            d=mosaic.put(d_piece),
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
            name_to_res[f'{self._resource_name}.system-fn'] = system_fn
            name_to_res[f'{self._resource_name}.{self._command_resource_suffix}'] = command
        return command


class UntypedCommandTemplateCtr(CommandTemplateCtr):

    @classmethod
    def from_piece(cls, piece, data_to_res):
        return cls(
            data_to_res=data_to_res,
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    @property
    def piece(self):
        return self._template_ctr_t(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.{self._command_resource_suffix}']

    def make_component(self, types, python_module, name_to_res=None):
        return self._make_command_component(types, python_module, name_to_res)

    @property
    def _resource_name(self):
        attr_name = '_'.join(self._attr_qual_name)
        return attr_name


class TypedCommandTemplateCtr(CommandTemplateCtr):

    @classmethod
    def from_piece(cls, piece, data_to_res):
        return cls(
            data_to_res=data_to_res,
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    def __init__(self, data_to_res, module_name, attr_qual_name, service_name, t, ctx_params, service_params):
        super().__init__(data_to_res, module_name, attr_qual_name, service_name, ctx_params, service_params)
        self._t = t

    @property
    def piece(self):
        return self._template_ctr_t(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
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
        attr_name = '_'.join(self._attr_qual_name)
        return f'{self._t.module_name}_{self._t.name}_{attr_name}'


class UiCommandTemplateCtr(TypedCommandTemplateCtr):

    _command_t = htypes.command.ui_command
    _template_ctr_t = htypes.command_resource.ui_command_template_ctr
    _is_global = False
    _command_resource_suffix = 'ui-command'


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
