from collections import defaultdict
from functools import partial

from . import htypes
from .services import (
    pyobj_creg,
    code_registry_ctr2,
    )


class ServiceTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            fn=pyobj_creg.invite(piece.function),
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, name, fn, free_params, service_params, want_config):
        self.service_name = name
        self.fn = fn
        self.free_params = free_params
        self.service_params = service_params
        self.want_config = want_config

    def __repr__(self):
        return f"<ServiceTemplate {self.service_name}: {self.fn} {self.free_params} {self.service_params} {self.want_config}>"

    @property
    def piece(self):
        return htypes.system.service_template(
            name=self.service_name,
            function=pyobj_creg.actor_to_ref(self.fn),
            free_params=tuple(self.free_params),
            service_params=tuple(self.service_params),
            want_config=self.want_config,
            )

    def resolve(self, system, service_name):
        if self.want_config:
            config_args = [system.resolve_config(self.service_name)]
        else:
            config_args = []
        service_args = [
            system.resolve_service(name)
            for name in self.service_params
            ]
        if self.free_params:
            return partial(self.fn, *config_args, *service_args)
        else:
            return self.fn(*config_args, *service_args)


class ServiceTemplateCfg:

    @classmethod
    def from_piece(cls, piece, system, service_name):
        template = ServiceTemplate.from_piece(piece)
        return cls(template)

    def __init__(self, template):
        self.key = template.service_name
        self.value = template


class System:

    def __init__(self):
        self._configs = defaultdict(dict)

    def update_config(self, service_name, config):
        self._configs[service_name].update(config)

    def run(self, root_name, *args, **kw):
        assert 0, (root_name, self._configs)


def load_config(system, config_piece):
    cfg_item_creg_config = {
        htypes.system.service_template: ServiceTemplateCfg.from_piece,
        }
    cfg_item_creg = code_registry_ctr2('cfg-item', cfg_item_creg_config)
    for sc in config_piece.services:
        for item_ref in sc.items:
            item = cfg_item_creg.invite(item_ref, system, sc.service)
            system.update_config(sc.service, {item.key: item.value})


def run_system(config, root_name, *args, **kw):
    system = System()
    load_config(system, config)
    system.run(root_name, *args, **kw)
