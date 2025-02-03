from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr
from .code.d_type import d_type


class CrudTemplateCtr(ModuleCtr):

    _service_name = 'crud_action'

    def __init__(self, module_name, attr_qual_name, model_t, action, key_fields, ctx_params, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._action = action
        self._key_fields = key_fields
        self._ctx_params = ctx_params
        self._service_params = service_params

    def update_resource_targets(self, resource_tgt, target_set):
        ready_tgt = target_set.factory.config_item_ready(self._service_name, self._resource_name)
        resolved_tgt = target_set.factory.config_item_resolved(self._service_name, self._resource_name)
        ready_tgt.set_provider(resource_tgt)
        resolved_tgt.resolve(self)

    @property
    def key_fields(self):
        return set(self._key_fields)

    def make_function(self, types, python_module, name_to_res):
        object = python_module
        prefix = []
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
            name_to_res['.'.join([*prefix, name])] = object
            prefix.append(name)
        system_fn = htypes.system_fn.ctx_fn(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        name_to_res[f'{self._resource_name}.system-fn'] = system_fn
        return system_fn

    def _make_resource_name(self, action):
        return f'{self._type_name}.crud.{action}'

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _resource_name(self):
        return self._make_resource_name(self._action)


class CrudInitTemplateCtr(CrudTemplateCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            action=piece.action,
            key_fields=piece.key_fields,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            commit_action=piece.commit_action,
            value_t=pyobj_creg.invite(piece.value_t),
            )

    def __init__(self, module_name, attr_qual_name, model_t, action, key_fields, ctx_params, service_params, commit_action, value_t):
        super().__init__(module_name, attr_qual_name, model_t, action, key_fields, ctx_params, service_params)
        self._commit_action = commit_action
        self._value_t = value_t

    @property
    def piece(self):
        return htypes.crud_ctr.init_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            action=self._action,
            key_fields=tuple(self._key_fields),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            commit_action=self._commit_action,
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        super().update_resource_targets(resource_tgt, target_set)
        self._add_open_command_targets(resource_tgt, target_set)

    def _add_open_command_targets(self, resource_tgt, target_set):
        if self._commit_action:
            commit_action = self._commit_action
            open_command_name = f'open_{self._commit_action}'
            commit_command_name = self._commit_action
        elif self._action == 'get':
            open_command_name = 'edit'
            commit_action = 'update'
            commit_command_name = 'save'
        else:
            assert 0, f"TODO: {self._action} action support"
        open_command_ctr = CrudOpenCommandCtr(
            module_name=self._module_name,
            model_t=self._model_t,
            name=open_command_name,
            value_t=self._value_t,
            commit_command_name=commit_command_name,
            commit_action=commit_action,
            )
        init_resolved_tgt = target_set.factory.config_item_resolved(
            self._service_name, self._make_resource_name(self._action))
        commit_resolved_tgt = target_set.factory.config_item_resolved(
            self._service_name, self._make_resource_name(commit_action))
        open_command_ctr.update_open_command_targets(resource_tgt, target_set, init_resolved_tgt, commit_resolved_tgt)


class CrudCommitTemplateCtr(CrudTemplateCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            action=piece.action,
            key_fields=piece.key_fields,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    @property
    def piece(self):
        return htypes.crud_ctr.commit_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            action=self._action,
            key_fields=tuple(self._key_fields),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )


class CrudOpenCommandCtr(ModuleCtr):

    def __init__(self, module_name, model_t, name, value_t, commit_command_name, commit_action):
        super().__init__(module_name)
        self._model_t = model_t
        self._name = name
        self._value_t = value_t
        self._commit_command_name = commit_command_name
        self._commit_action = commit_action
        self._init_resolved_tgt = None
        self._commit_resolved_tgt = None

    def update_open_command_targets(self, resource_tgt, target_set, init_resolved_tgt, commit_resolved_tgt):
        _, resolved_tgt, _ = target_set.factory.config_items(
            'model_command_reg', self._resource_name, provider=resource_tgt, ctr=self)
        resolved_tgt.add_dep(init_resolved_tgt)
        resolved_tgt.add_dep(commit_resolved_tgt)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        self._init_resolved_tgt = init_resolved_tgt
        self._commit_resolved_tgt = commit_resolved_tgt

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.command-cfg-item']

    def _command_d(self, types, name):
        code_name = self._module_name.split('.')[-1]
        d_t = d_type(types, code_name, name)
        return d_t()

    def make_component(self, types, python_module, name_to_res):
        key_fields = sorted(
            self._init_resolved_tgt.constructor.key_fields
            | self._commit_resolved_tgt.constructor.key_fields
            )
        init_action_fn = self._init_resolved_tgt.constructor.make_function(
            types, python_module, name_to_res)
        commit_action_fn = self._commit_resolved_tgt.constructor.make_function(
            types, python_module, name_to_res)
        commit_command_d = self._command_d(types, self._commit_command_name)
        system_fn = htypes.crud.open_command_fn(
            name=self._name,
            value_t=pyobj_creg.actor_to_ref(self._value_t),
            key_fields=tuple(key_fields),
            init_action_fn=mosaic.put(init_action_fn),
            commit_command_d=mosaic.put(commit_command_d),
            commit_action_fn=mosaic.put(commit_action_fn),
            )
        open_command_d = self._command_d(types, self._name)
        properties = htypes.command.properties(
            is_global=False,
            uses_state=True,
            remotable=False,
            )
        command = htypes.command.model_command(
            d=mosaic.put(open_command_d),
            properties=properties,
            system_fn=mosaic.put(system_fn),
            )
        cfg_item = htypes.command.cfg_item(
            t=pyobj_creg.actor_to_ref(self._model_t),
            command=mosaic.put(command),
            )
        name_to_res[f'{self._resource_name}.open-command.d'] = open_command_d
        name_to_res[f'{self._resource_name}.commit-command.d'] = commit_command_d
        name_to_res[f'{self._resource_name}.command-fn'] = system_fn
        name_to_res[f'{self._resource_name}.command'] = command
        name_to_res[f'{self._resource_name}.command-cfg-item'] = cfg_item

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.{self._name}'
