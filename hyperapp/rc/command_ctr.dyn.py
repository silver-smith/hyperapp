from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor


STATE_PARAMS = {'state', 'model_state', 'current_item', 'current_idx', 'current_path'}
LOCAL_PARAMS = {'controller', 'ctx', 'lcs', 'rpc_endpoint', 'identity', 'remote_peer'}


class CommandTemplateCtr(Constructor):

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
        self._data_to_res = data_to_res
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._t = t
        self._ctx_params = ctx_params
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.command_resource.command_template_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            t=pyobj_creg.actor_to_ref(self._t),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )

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

    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.ui-command']

    def make_component(self, types, python_module, name_to_res=None):
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
        d_name = self._attr_qual_name[-1] + '_d'
        type_module = self._module_name.split('.')[-1]
        d_t_piece = types.get(type_module, d_name)
        assert d_t_piece, (type_module, d_name)  # TODO: Make type if missing.
        d_t = pyobj_creg.animate(d_t_piece)
        d_piece = self._data_to_res(d_t())
        impl = htypes.ui.ui_command_impl(
            function=mosaic.put(object),
            ctx_params=tuple(self._ctx_params),
            service_params=tuple(self._service_params),
            )
        properties = htypes.ui.command_properties(
            is_global=False,
            uses_state=bool(set(self._ctx_params) & STATE_PARAMS),
            remotable=not set(self._ctx_params) & LOCAL_PARAMS,
            )
        command = htypes.ui.ui_command(
            d=mosaic.put(d_piece),
            properties=properties,
            impl=mosaic.put(impl),
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.d'] = d_piece
            name_to_res[f'{self._resource_name}.ui-command-impl'] = impl
            name_to_res[f'{self._resource_name}.command-properties'] = properties
            name_to_res[f'{self._resource_name}.ui-command'] = command
        return command

    @property
    def _resource_name(self):
        attr_name = '_'.join(self._attr_qual_name)
        return f'{self._t.module_name}_{self._t.name}_{attr_name}'
