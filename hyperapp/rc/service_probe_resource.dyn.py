from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.rc_constructor import ModuleCtr
from .code.rc_resource import Resource
from .code.system_probe import Probe
from .code.config_item_resource import ConfigItemResource
from .code.service_ctr import ServiceTemplateCtr, FinalizerGenServiceTemplateCtr
from .code.service_req import ServiceReq


class ServiceProbe(Probe):

    def __init__(self, system_probe, config_ctl, attr_name, service_name, ctl_ref, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._config_ctl = config_ctl
        self._attr_name = attr_name
        self._ctl_ref = ctl_ref

    def __repr__(self):
        return f"<ServiceProbe {self._attr_name} {self._fn} {self._params}>"

    def _add_service_constructor(self, params, is_gen):
        if is_gen:
            ctr_cls = FinalizerGenServiceTemplateCtr
            kw = {}
        else:
            ctr_cls = ServiceTemplateCtr
            kw = dict(
                free_params=params.free_names,
                )
        ctr = ctr_cls(
            config_ctl=self._config_ctl,
            attr_name=self._attr_name,
            name=self._name,
            ctl_ref=self._ctl_ref,
            service_params=params.service_names,
            want_config=params.has_config,
            **kw,
            )
        self._system.add_constructor(ctr)


def resolve_service_probe_cfg_item(piece):
    return (piece.service_name, piece)


def resolve_service_probe_cfg_value(piece, key, system, service_name):
    config_ctl = system.resolve_service('config_ctl')
    fn = pyobj_creg.invite(piece.function)
    probe = ServiceProbe(system, config_ctl, piece.attr_name, piece.service_name, piece.ctl, fn, piece.params)
    probe.apply_if_no_params()
    return probe


class ServiceProbeCtr(ModuleCtr):

    @classmethod
    def from_piece(cls, piece, config_ctl):
        return cls(
            config_ctl,
            piece.module_name,
            piece.attr_name,
            piece.name,
            piece.ctl,
            piece.is_generator_fn,
            piece.params,
            )

    def __init__(self, config_ctl, module_name, attr_name, name, ctl_ref, is_generator_fn, params):
        super().__init__(module_name)
        self._config_ctl = config_ctl
        self._attr_name = attr_name
        self._name = name
        self._ctl_ref = ctl_ref
        self._is_generator_fn = is_generator_fn
        self._params = params

    @property
    def piece(self):
        return htypes.service_resource.service_probe_ctr(
            module_name=self._module_name,
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl_ref,
            is_generator_fn=self._is_generator_fn,
            params=self._params,
            )

    def update_resource_targets(self, resource_tgt, target_set):
        resource_tgt.import_tgt.add_test_ctr(self)
        if tuple(self._params) in {(), ('config',)}:
            ctr_kw = dict(
                config_ctl=self._config_ctl,
                attr_name=self._attr_name,
                name=self._name,
                ctl_ref=self._ctl_ref,
                service_params=[],
                want_config='config' in self._params,
                )
            if self._is_generator_fn:
                template_ctr = FinalizerGenServiceTemplateCtr(
                    **ctr_kw,
                    )
            else:
                template_ctr = ServiceTemplateCtr(
                    **ctr_kw,
                    free_params=[],
                    )
        else:
            template_ctr = None
        req = ServiceReq(self._name)
        ready_tgt, resolved_tgt, _ = target_set.factory.config_items(
            'system', self._name, req, provider=resource_tgt, ctr=template_ctr)
        resource_tgt.add_cfg_item_target(resolved_tgt)

    def make_component(self, types, python_module, name_to_res=None):
        function = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        return htypes.service_resource.service_probe_template(
            attr_name=self._attr_name,
            service_name=self._name,
            ctl=self._ctl_ref,
            function=mosaic.put(function),
            params=self._params,
            )

    def make_resource(self, types, module_name, python_module):
        item = self.make_component(types, python_module)
        return ConfigItemResource(
            service_name='system',
            template_ref=mosaic.put(item),
            )
