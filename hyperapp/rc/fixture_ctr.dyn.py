from . import htypes
from .services import (
    mosaic,
    )
from .code.rc_constructor import ModuleCtr
from .code.config_item_resource import ConfigItemResource
from .code.fixture_resource import ConfigFixtureResource


class FixtureCtrBase(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            module_name=piece.module_name,
            attr_name=piece.attr_name,
            name=piece.name,
            ctl_ref=piece.ctl,
            params=piece.params,
            )

    def __init__(self, module_name, attr_name, name, ctl_ref, params):
        super().__init__(module_name)
        self._attr_name = attr_name
        self._name = name
        self._ctl_ref = ctl_ref
        self._params = params

    @property
    def is_fixture(self):
        return True

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        assert import_alias_tgt.module_name == self._module_name
        import_alias_tgt.add_component(self)

    def make_resource(self, types, module_name, python_module):
        item = self.make_component(types, python_module)
        return ConfigItemResource(
            service_name='system',
            template_ref=mosaic.put(item),
            )


class FixtureObjCtr(FixtureCtrBase):

    @property
    def piece(self):
        return htypes.fixture_resource.fixture_obj_ctr(
            module_name=self._module_name,
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl_ref,
            params=self._params,
            )

    def make_component(self, types, python_module, name_to_res=None):
        function = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        return htypes.fixture_resource.fixture_obj_template(
            service_name=self._name,
            ctl=self._ctl_ref,
            function=mosaic.put(function),
            params=self._params,
            )


class FixtureProbeCtr(FixtureCtrBase):

    @property
    def piece(self):
        return htypes.fixture_resource.fixture_probe_ctr(
            module_name=self._module_name,
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl_ref,
            params=self._params,
            )

    def make_component(self, types, python_module, name_to_res=None):
        function = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        return htypes.fixture_resource.fixture_probe_template(
            service_name=self._name,
            ctl=self._ctl_ref,
            function=mosaic.put(function),
            params=self._params,
            )


class ConfigFixtureCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece):
        return cls(piece.module_name, piece.attr_qual_name, piece.service_name, piece.service_params)

    def __init__(self, module_name, attr_qual_name, service_name, service_params):
        super().__init__(module_name)
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.fixture_resource.config_fixture_ctr(
            module_name=self._module_name,
            attr_qual_name=tuple(self._attr_qual_name),
            service_name=self._service_name,
            service_params=self._service_params,
            )

    @property
    def is_fixture(self):
        return True

    def update_fixtures_targets(self, import_alias_tgt, target_set):
        assert import_alias_tgt.module_name == self._module_name
        import_alias_tgt.add_component(self)

    def make_component(self, types, python_module, name_to_res=None):
        object = python_module
        for name in self._attr_qual_name:
            object = htypes.builtin.attribute(
                object=mosaic.put(object),
                attr_name=name,
                )
        return object

    def make_resource(self, types, module_name, python_module):
        return ConfigFixtureResource(self._service_name, self.make_component(types, python_module), self._service_params)
