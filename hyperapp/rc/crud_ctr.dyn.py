from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import ModuleCtr


class CrudTemplateCtr(ModuleCtr):

    def __init__(self, data_to_res, module_name, attr_qual_name, model_t, action, key_field, crud_params, service_params):
        super().__init__(module_name)
        self._data_to_res = data_to_res
        self._attr_qual_name = attr_qual_name
        self._model_t = model_t
        self._action = action
        self._key_field = key_field
        self._crud_params = crud_params
        self._service_params = service_params

    # def get_component(self, name_to_res):
    #     return name_to_res[self._resource_name]

    # def make_component(self, types, python_module, name_to_res):
    #     object = python_module
    #     for name in self._attr_qual_name:
    #         object = htypes.builtin.attribute(
    #             object=mosaic.put(object),
    #             attr_name=name,
    #             )

    # @property
    # def _type_name(self):
    #     return f'{self._model_t.module_name}-{self._model_t.name}'

    # @property
    # def _resource_name(self):
    #     return f'{self._type_name}.edit.command-cfg-item'


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
            crud_params=piece.crud_params,
            service_params=piece.service_params,
            record_t=pyobj_creg.invite(piece.record_t),
            )

    def __init__(self, data_to_res, module_name, attr_qual_name, model_t, action, key_field, crud_params, service_params, record_t):
        super().__init__(data_to_res, module_name, attr_qual_name, model_t, action, key_field, crud_params, service_params)
        self._record_t = record_t

    @property
    def piece(self):
        return htypes.crud_ctr.init_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            action=self._action,
            key_field=self._key_field,
            crud_params=tuple(self._crud_params),
            service_params=tuple(self._service_params),
            record_t=pyobj_creg.actor_to_ref(self._record_t),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        if self._action == 'get':
            open_command_name = 'edit'
            commit_action = 'update'
        else:
            assert 0, f"TODO: {self._action} action support"
        open_command_ctr = CrudOpenCommandCtr(
            data_to_res=self._data_to_res,
            module_name=self._module_name,
            model_t=self._model_t,
            name=open_command_name,
            key_field=self._key_field,
            init_action=self._action,
            commit_action=commit_action,
            )
        open_command_ctr.update_resource_targets(resource_tgt, target_set)


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
            crud_params=piece.crud_params,
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
            crud_params=tuple(self._crud_params),
            service_params=tuple(self._service_params),
            )

    def update_resource_targets(self, resource_tgt, target_set):
        pass
        # _, resolved_tgt, _ = target_set.factory.config_items(
        #     'model_command_reg', self._resource_name, provider=resource_tgt, ctr=self)
        # resource_tgt.add_cfg_item_target(resolved_tgt)


class CrudOpenCommandCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece, data_to_res):
        return cls(
            data_to_res=data_to_res,
            module_name=piece.module_name,
            model_t=pyobj_creg.invite(piece.model_t),
            name=piece.name,
            key_field=piece.key_field,
            init_action=piece.commit_action,
            commit_action=piece.commit_action,
            )

    def __init__(self, data_to_res, module_name, model_t, name, key_field, init_action, commit_action):
        super().__init__(module_name)
        self._data_to_res = data_to_res
        self._model_t = model_t
        self._name = name
        self._key_field = key_field
        self._init_action = init_action
        self._commit_action = commit_action

    @property
    def piece(self):
        return htypes.crud_ctr.open_command_ctr(
            module_name=self._module_name,
            model_t=pyobj_creg.actor_to_ref(self._model_t),
            name=self._name,
            key_field=self._key_field,
            init_action=self._init_action,
            commit_action=self._commit_action,
            )

    def update_resource_targets(self, resource_tgt, target_set):
        _, resolved_tgt, _ = target_set.factory.config_items(
            'model_command_reg', self._resource_name, provider=resource_tgt, ctr=self)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def get_component(self, name_to_res):
        return name_to_res[self._resource_name]

    def make_component(self, types, python_module, name_to_res):
        system_fn = htypes.crud.crud_open_command_fn(
            name=self._name,
            key_field=self._key_field,
            init_action=self._init_action,
            commit_action=self._commit_action,
            )
        d_name = f'{self._name}_d'
        d_t_piece = types.get('crud', d_name)
        assert d_t_piece, d_name  # TODO: Make type if missing.
        d_t = pyobj_creg.animate(d_t_piece)
        d_piece = self._data_to_res(d_t())
        properties = htypes.command.properties(
            is_global=False,
            uses_state=True,
            remotable=False,
            )
        command = htypes.command.model_command(
            d=mosaic.put(d_piece),
            properties=properties,
            system_fn=mosaic.put(system_fn),
            )
        cfg_item = htypes.command.cfg_item(
            t=pyobj_creg.actor_to_ref(self._model_t),
            command=mosaic.put(command),
            )
        name_to_res[f'{self._type_name}.{self._name}.command.d'] = d_piece
        name_to_res[f'{self._type_name}.{self._name}.command.fn'] = system_fn
        name_to_res[f'{self._type_name}.{self._name}.command'] = command
        name_to_res[self._resource_name] = cfg_item

    @property
    def _type_name(self):
        return f'{self._model_t.module_name}-{self._model_t.name}'

    @property
    def _resource_name(self):
        return f'{self._type_name}.edit.command-cfg-item'
