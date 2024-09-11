from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_constructor import Constructor, ModuleCtr


class ServiceCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name)

    def __init__(self, attr_name, name):
        self._attr_name = attr_name
        self._name = name

    def update_resource_targets(self, resource_tgt, target_set):
        service_found_tgt = target_set.factory.service_found(self._name)
        service_found_tgt.set_provider(resource_tgt, self, target_set)
        resolved_tgt = target_set.factory.service_resolved(self._name)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        resolved_tgt.resolve(self)
        target_set.update_deps_for(service_found_tgt)
        target_set.update_deps_for(resolved_tgt)
        target_set.update_deps_for(resource_tgt)

    def make_component(self, types, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        service = htypes.builtin.call(
            function=mosaic.put(attribute),
            )
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'{self._name}.service'] = service
        return service

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.service']


class ServiceTemplateCtrBase(Constructor):

    def __init__(self, name):
        self._name = name

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.service']


class CoreServiceTemplateCtr(ServiceTemplateCtrBase):

    @classmethod
    def from_template_piece(cls, piece):
        return cls(piece.name)


class ServiceTemplateCtr(ServiceTemplateCtrBase):

    @classmethod
    def from_piece(cls, piece, config_ctl_creg):
        ctl = config_ctl_creg.invite(piece.ctl)
        return cls(
            attr_name=piece.attr_name,
            name=piece.name,
            ctl=ctl,
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, attr_name, name, ctl, free_params, service_params, want_config):
        super().__init__(name)
        self._attr_name = attr_name
        self._ctl = ctl
        self._free_params = free_params
        self._service_params = service_params
        self._want_config = want_config

    @property
    def piece(self):
        return htypes.rc_constructors.service_template(
            attr_name=self._attr_name,
            name=self._name,
            ctl=mosaic.put(self._ctl.piece),
            free_params=tuple(self._free_params),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )

    def update_targets(self, target_set):
        resolved_tgt = target_set.factory.config_item_resolved('system', self._name)
        resolved_tgt.resolve(self)
        target_set.update_deps_for(resolved_tgt)
        # Should be created to be added to config resource.
        _ = target_set.factory.config_item_complete('system', self._name)

    def make_component(self, types, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        ctl = htypes.system.item_dict_config_ctl()  # TODO: Add parameter to marker.
        service = htypes.system.service_template(
            name=self._name,
            ctl=mosaic.put(self._ctl.piece),
            function=mosaic.put(attribute),
            free_params=tuple(self._free_params),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'item-dict-config.ctl'] = ctl
            name_to_res[f'{self._name}.service'] = service
        return service
