from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_constructor import Constructor
from .code.service_probe_resource import ConfigItemFixtureResource, FixtureProbeResource, ServiceProbeResource


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

    def make_component(self, python_module, name_to_res=None):
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


class ServiceProbeCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name, piece.params)

    def __init__(self, attr_name, name, params):
        self._attr_name = attr_name
        self._name = name
        self._params = params

    def update_resource_targets(self, resource_tgt, target_set):
        resource_tgt.import_alias_tgt.add_component(self)
        ready_tgt = target_set.factory.config_item_ready('system', self._name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved('system', self._name)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(ready_tgt)
        target_set.update_deps_for(resource_tgt)

    def make_component(self, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def make_resource(self, module_name, python_module):
        return ServiceProbeResource(self._attr_name, self._name, self.make_component(python_module), self._params)


class ServiceTemplateCtr(Constructor):

    @classmethod
    def from_template(cls, service_name, template):
        return cls(
            attr_name=template.attr_name,
            name=service_name,
            free_params=template.free_params,
            service_params=template.service_params,
            want_config=template.want_config,
            )

    @classmethod
    def from_piece(cls, piece):
        return cls(
            attr_name=piece.attr_name,
            name=piece.name,
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, attr_name, name, free_params, service_params, want_config):
        self._attr_name = attr_name
        self._name = name
        self.free_params = free_params
        self.service_params = service_params
        self.want_config = want_config

    @property
    def piece(self):
        return htypes.rc_constructors.service_template(
            attr_name=self._attr_name,
            name=self._name,
            free_params=tuple(self.free_params),
            service_params=tuple(self.service_params),
            want_config=self.want_config,
            )

    def update_targets(self, target_set):
        resolved_tgt = target_set.factory.config_item_resolved('system', self._name)
        resolved_tgt.resolve(self)
        target_set.update_deps_for(resolved_tgt)

    def make_component(self, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        service = htypes.system.service_template(
            name=self._name,
            function=mosaic.put(attribute),
            free_params=tuple(self.free_params),
            service_params=tuple(self.service_params),
            want_config=self.want_config,
            )
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'{self._name}.service'] = service
        return service

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.service']


class FixtureCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.name, piece.params)

    def __init__(self, attr_name, name, params):
        self._attr_name = attr_name
        self._name = name
        self._params = params

    @property
    def is_fixture(self):
        return True

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        import_alias_tgt.add_component(self)

    def make_component(self, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def make_resource(self, module_name, python_module):
        return FixtureProbeResource(self._name, self.make_component(python_module), self._params)


class ConfigItemFixtureCtr(Constructor):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.attr_name, piece.service_name, piece.service_params)

    def __init__(self, attr_name, service_name, service_params):
        self._attr_name = attr_name
        self._service_name = service_name
        self._service_params = service_params

    @property
    def is_fixture(self):
        return True

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        import_alias_tgt.add_component(self)

    def make_component(self, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def make_resource(self, module_name, python_module):
        return ConfigItemFixtureResource(self._service_name, self.make_component(python_module), self._service_params)
