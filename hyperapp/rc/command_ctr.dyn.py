from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    )
from .code.rc_constructor import Constructor


class CommandTemplateCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_qual_name=piece.attr_qual_name,
            service_name=piece.service_name,
            t=pyobj_creg.invite(piece.t),
            ctx_params=piece.ctx_params,
            service_params=piece.service_params,
            )

    def __init__(self, module_name, attr_qual_name, service_name, t, ctx_params, service_params):
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

    # Ever used?
    def get_component(self, name_to_res):
        return name_to_res[f'{self._resource_name}.actor-template']

    def make_component(self, python_module, name_to_res=None):
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
        template = htypes.system.actor_template(
            t=pyobj_creg.actor_to_ref(self._t),
            function=mosaic.put(object),
            service_params=tuple(self._service_params),
            )
        if name_to_res is not None:
            name_to_res[f'{self._resource_name}.actor-template'] = template
        return template

    @property
    def _resource_name(self):
        attr_name = '_'.join(self._attr_qual_name)
        return f'{self._t.module_name}_{self._t.name}_{attr_name}'
