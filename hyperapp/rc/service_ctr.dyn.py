from . import htypes
from .services import (
    deduce_t,
    mosaic,
    web,
    )
from .code.rc_constructor import Constructor, ModuleCtr


class CoreServiceTemplateCtr(Constructor):

    @classmethod
    def from_template_piece(cls, piece):
        return cls(piece.name)

    def __init__(self, name):
        self._name = name

    def get_component(self, name_to_res):
        return name_to_res[f'{self._name}.service']


class ServiceTemplateCtrBase(CoreServiceTemplateCtr):

    def __init__(self, config_ctl, attr_name, name, ctl_ref, service_params, want_config):
        super().__init__(name)
        self._config_ctl = config_ctl
        self._attr_name = attr_name
        self._ctl_ref = ctl_ref
        self._service_params = service_params
        self._want_config = want_config

    def update_targets(self, target_set):
        resolved_tgt = target_set.factory.config_item_resolved('system', self._name)
        resolved_tgt.resolve(self)
        target_set.update_deps_for(resolved_tgt)
        # Complete target should be created so it will be added to config resource.
        _ = target_set.factory.config_item_complete('system', self._name)

    def make_component(self, types, python_module, name_to_res=None):
        attribute = htypes.builtin.attribute(
            object=mosaic.put(python_module),
            attr_name=self._attr_name,
            )
        service = self._template_t(
            name=self._name,
            ctl=self._ctl_ref,
            function=mosaic.put(attribute),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            **self._template_kw(),
            )
        ctl = web.summon(self._ctl_ref)
        ctl_t = deduce_t(ctl)
        ctl_t_name = ctl_t.full_name.replace('.', '-')
        if name_to_res is not None:
            name_to_res[self._attr_name] = attribute
            name_to_res[f'{ctl_t_name}.ctl'] = web.summon(self._ctl_ref)
            name_to_res[f'{self._name}.service'] = service
        return service

    def _template_kw(self):
        return {}


class ServiceTemplateCtr(ServiceTemplateCtrBase):

    _template_ctr_t = htypes.service_resource.service_template_ctr
    _template_t = htypes.system.service_template

    @classmethod
    def from_piece(cls, piece, config_ctl):
        return cls(
            config_ctl=config_ctl,
            attr_name=piece.attr_name,
            name=piece.name,
            ctl_ref=piece.ctl,
            service_params=piece.service_params,
            want_config=piece.want_config,
            free_params=piece.free_params,
            )

    def __init__(self, config_ctl, attr_name, name, ctl_ref, service_params, want_config, free_params):
        super().__init__(config_ctl, attr_name, name, ctl_ref, service_params, want_config)
        self._free_params = free_params

    @property
    def piece(self):
        return self._template_ctr_t(
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl_ref,
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            free_params=tuple(self._free_params),
            )

    def _template_kw(self):
        return dict(
            free_params=tuple(self._free_params),
            )


class FinalizerGenServiceTemplateCtr(ServiceTemplateCtrBase):

    _template_ctr_t = htypes.service_resource.finalizer_gen_service_template_ctr
    _template_t = htypes.system.finalizer_gen_service_template

    @classmethod
    def from_piece(cls, piece, config_ctl):
        return cls(
            config_ctl=config_ctl,
            attr_name=piece.attr_name,
            name=piece.name,
            ctl_ref=piece.ctl,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    @property
    def piece(self):
        return self._template_ctr_t(
            attr_name=self._attr_name,
            name=self._name,
            ctl=self._ctl_ref,
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )
