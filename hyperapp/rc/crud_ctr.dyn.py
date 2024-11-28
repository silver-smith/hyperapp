from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class CrudTemplateCtr(ModuleCtr):

    def __init__(self, data_to_res, module_name, attr_qual_name, model_t, action, key_field, ctx_params, service_params):
        super().__init__(module_name)
        self._data_to_res = data_to_res
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._action = action
        self._key_field = key_field
        self._ctx_params = ctx_params
        self._service_params = service_params


class CrudInitTemplateCtr(CrudTemplateCtr):

    @classmethod
    def from_piece(cls, piece, data_to_res):
        return cls(
            data_to_res=data_to_res,
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            action=piece.action,
            key_field=piece.key_field,
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            record_t=pyobj_creg.invite(piece.record_t),
            )

    def __init__(self, data_to_res, module_name, attr_qual_name, model_t, action, key_field, ctx_params, service_params, record_t):
        super().__init__(data_to_res, module_name, attr_qual_name, model_t, action, key_field, ctx_params, service_params)
        self._record_t = record_t

    @property
    def piece(self):
        return htypes.crud_ctr.init_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            action=self._action,
            key_field=self._key_field,
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            record_t=pyobj_creg.actor_to_ref(self._record_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        service_name = 'crud_action'
        ready_tgt = target_set.factory.config_item_ready(service_name, self._resource_name)
        resolved_tgt = target_set.factory.config_item_resolved(service_name, self._resource_name)
        ready_tgt.set_provider(resource_tgt)
        resolved_tgt.resolve(self)
        self._add_open_command_targets(resource_tgt, target_set, resolved_tgt)

    def _add_open_command_targets(self, resource_tgt, target_set, resolved_tgt):
        if self._action == 'get':
            open_command_name = 'edit'
            commit_action = 'update'
            commit_command_name = 'save'
        else:
            assert 0, f"TODO: {self._action} action support"
        open_command_ctr = CrudOpenCommandCtr(
            data_to_res=self._data_to_res,
            module_name=self._module_name,
            model_t=self._model_t,
            name=open_command_name,
            record_t=self._record_t,
            key_field=self._key_field,
            commit_command_name=commit_command_name,
            commit_action=commit_action,
            )
        open_command_ctr.update_open_command_targets(resource_tgt, target_set, resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[self._resource_name]

    def make_component(self, types, python_module, name_to_res):
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
        name_to_res[f'{self._resource_name}'] = system_fn
        return system_fn

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.crud.{self._action}.system-fn'


class CrudCommitTemplateCtr(CrudTemplateCtr):

    @classmethod
    def from_piece(cls, piece, data_to_res):
        return cls(
            data_to_res=data_to_res,
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            model_t=pyobj_creg.invite(piece.model_t),
            action=piece.action,
            key_field=piece.key_field,
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
            key_field=self._key_field,
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        pass


class CrudOpenCommandCtr(ModuleCtr):

    def __init__(self, data_to_res, module_name, model_t, name, record_t, key_field, commit_command_name, commit_action):
        super().__init__(module_name)
        self._data_to_res = data_to_res
        self._model_t = model_t
        self._name = name
        self._record_t = record_t
        self._key_field = key_field
        self._commit_command_name = commit_command_name
        self._commit_action = commit_action
        self._init_resolved_tgt = None

    def update_open_command_targets(self, resource_tgt, target_set, init_resolved_tgt):
        _, resolved_tgt, _ = target_set.factory.config_items(
            'model_command_reg', self._resource_name, provider=resource_tgt, ctr=self)
        resolved_tgt.add_dep(init_resolved_tgt)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        self._init_resolved_tgt = init_resolved_tgt

    def get_component(self, name_to_res):
        return name_to_res[self._resource_name]

    def _command_d_piece(self, types, name):
        d_name = f'{name}_d'
        d_t_piece = types.get('crud', d_name)
        assert d_t_piece, d_name  # TODO: Make type if missing.
        d_t = pyobj_creg.animate(d_t_piece)
        return self._data_to_res(d_t())

    def make_component(self, types, python_module, name_to_res):
        init_action_fn = self._init_resolved_tgt.constructor.make_component(
            types, python_module, name_to_res)
        commit_command_d_piece = self._command_d_piece(types, self._commit_command_name)
        system_fn = htypes.crud.open_command_fn(
            name=self._name,
            record_t=pyobj_creg.actor_to_ref(self._record_t),
            key_field=self._key_field,
            init_action_fn=mosaic.put(init_action_fn),
            commit_command_d=mosaic.put(commit_command_d_piece),
            commit_action=self._commit_action,
            )
        open_command_d_piece = self._command_d_piece(types, self._name)
        properties = htypes.command.properties(
            is_global=False,
            uses_state=True,
            remotable=False,
            )
        command = htypes.command.model_command(
            d=mosaic.put(open_command_d_piece),
            properties=properties,
            system_fn=mosaic.put(system_fn),
            )
        cfg_item = htypes.command.cfg_item(
            t=pyobj_creg.actor_to_ref(self._model_t),
            command=mosaic.put(command),
            )
        name_to_res[f'{self._type_name}.{self._name}.open-command.d'] = open_command_d_piece
        name_to_res[f'{self._type_name}.{self._name}.commit-command.d'] = commit_command_d_piece
        name_to_res[f'{self._type_name}.{self._name}.command.fn'] = system_fn
        name_to_res[f'{self._type_name}.{self._name}.command'] = command
        name_to_res[self._resource_name] = cfg_item

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.edit.command-cfg-item'
