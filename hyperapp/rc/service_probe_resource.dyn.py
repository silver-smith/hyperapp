from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_constructor import ModuleCtr
from .code.rc_resource import Resource
from .code.system_probe import Probe
from .code.service_ctr import ServiceTemplateCtr


class ServiceProbe(Probe):

    def __init__(self, system_probe, config_ctl, attr_name, service_name, ctl, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._config_ctl = config_ctl
        self._attr_name = attr_name
        self._ctl = ctl

    def __repr__(self):
        return f"<ServiceProbe {self._attr_name} {self._fn} {self._params} {self._ctl}>"

    def _add_constructor(self, want_config, service_params):
        free_params_ofs = len(service_params)
        if want_config:
            free_params_ofs += 1
        ctr = ServiceTemplateCtr(
            config_ctl=self._config_ctl,
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl,
            free_params=self._params[free_params_ofs:],
            service_params=service_params,
            want_config=want_config,
            )
        self._system.add_constructor(ctr)


class ServiceProbeTemplate:

    def __init__(self, attr_name, ctl, fn_piece, params):
        self._attr_name = attr_name
        self._ctl = ctl
        self._fn = fn_piece
        self._params = params

    def __repr__(self):
        return f"<ServiceProbeTemplate {self._attr_name} {self._fn} {self._params} {self._ctl}>"

    @property
    def ctl(self):
        return self._ctl

    def resolve(self, system, service_name):
        config_ctl = system.resolve_service('config_ctl')
        fn = pyobj_creg.animate(self._fn)
        probe = ServiceProbe(system, config_ctl, self._attr_name, service_name, self._ctl, fn, self._params)
        probe.apply_if_no_params()
        return probe


class ServiceProbeResource(Resource):

    @classmethod
    def from_piece(cls, piece, config_ctl_creg):
        ctl = config_ctl_creg.invite(piece.ctl)
        return cls(piece.attr_name, piece.service_name, ctl, web.summon(piece.function), piece.params)

    def __init__(self, attr_name, service_name, ctl, function, params):
        self._attr_name = attr_name
        self._service_name = service_name
        self._ctl = ctl
        self._function = function  # piece
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_resource(
            attr_name=self._attr_name,
            service_name=self._service_name,
            ctl=mosaic.put(self._ctl.piece),
            function=mosaic.put(self._function),
            params=tuple(self._params),
            )

    @property
    def is_system_resource(self):
        return True

    def configure_system(self, system):
        probe = ServiceProbeTemplate(self._attr_name, self._ctl, self._function, self._params)
        system.update_config('system', {self._service_name: probe})


class ServiceProbeCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece, config_ctl_creg, config_ctl):
        ctl = config_ctl_creg.invite(piece.ctl)
        return cls(config_ctl, piece.module_name, piece.attr_name, piece.name, ctl, piece.params)

    def __init__(self, config_ctl, module_name, attr_name, name, ctl, params):
        super().__init__(module_name)
        self._config_ctl = config_ctl
        self._attr_name = attr_name
        self._name = name
        self._ctl = ctl
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_ctr(
            module_name=self._module_name,
            attr_name=self._attr_name,
            name=self._name,
            ctl=mosaic.put(self._ctl.piece),
            params=self._params,
            )

    def update_resource_targets(self, resource_tgt, target_set):
        resource_tgt.import_alias_tgt.add_component(self)
        ready_tgt = target_set.factory.config_item_ready('system', self._name)
        ready_tgt.set_provider(resource_tgt, target_set)
        resolved_tgt = target_set.factory.config_item_resolved('system', self._name)
        resource_tgt.add_cfg_item_target(resolved_tgt)
        target_set.update_deps_for(ready_tgt)
        target_set.update_deps_for(resource_tgt)
        if tuple(self._params) not in {(), ('config',)}:
            return
        template_ctr = ServiceTemplateCtr(
            config_ctl=self._config_ctl,
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl,
            free_params=[],
            service_params=[],
            want_config='config' in self._params,
            )
        resolved_tgt.resolve(template_ctr)
        target_set.update_deps_for(resolved_tgt)
        # Should be created to be added to config resource.
        _ = target_set.factory.config_item_complete('system', self._name)
        self._config_ctl[self._name] = self._ctl

    def make_component(self, types, python_module, name_to_res=None):
        return htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )

    def make_resource(self, types, module_name, python_module):
        return ServiceProbeResource(self._attr_name, self._name, self._ctl, self.make_component(types, python_module), self._params)
