import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass
from functools import partial

from hyperapp.boot.htypes import Type

from . import htypes
from .services import (
    cached_code_registry_ctr,
    code_registry_ctr,
    pyobj_creg,
    web,
    )
from .code.config_ctl import DictConfigCtl, service_pieces_to_config
from .code.config_layer import ProjectConfigLayer, StaticConfigLayer

log = logging.getLogger(__name__)


class ServiceDepLoopError(Exception):
    pass


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


@dataclass
class ActorRequester:

    actor_t: Type

    def __str__(self):
        return f"Actor {self.actor_t.full_name}"


class ServiceTemplateBase:

    def __init__(self, name, ctl_ref, fn, service_params, want_config):
        self.service_name = name
        self._ctl_ref = ctl_ref
        self._fn = fn
        self._service_params = service_params
        self._want_config = want_config

    @property
    def key(self):
        return self.service_name

    @property
    def ctl_ref(self):
        return self._ctl_ref

    def _resolve_service_args(self, system):
        if self._want_config:
            config_args = [system.resolve_config(self.service_name)]
        else:
            config_args = []
        service_args = [
            system.resolve_service(name)
            for name in self._service_params
            ]
        return [*config_args, *service_args]


class ServiceTemplate(ServiceTemplateBase):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            ctl_ref=piece.ctl,
            fn=pyobj_creg.invite(piece.function),
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, name, ctl_ref, fn, free_params, service_params, want_config):
        super().__init__(name, ctl_ref, fn, service_params, want_config)
        self._free_params = free_params

    def __repr__(self):
        return f"<ServiceTemplate {self.service_name}: {self._fn} {self._free_params} {self._service_params} {self._want_config}>"

    @property
    def piece(self):
        return htypes.system.service_template(
            name=self.service_name,
            ctl=self._ctl_ref,
            function=pyobj_creg.actor_to_ref(self._fn),
            free_params=tuple(self._free_params),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )

    def resolve(self, system, service_name):
        service_args = self._resolve_service_args(system)
        if self._free_params:
            return partial(self._fn, *service_args)
        else:
            return self._fn(*service_args)


class FinalizerGenServiceTemplate(ServiceTemplateBase):

    @classmethod
    def from_piece(cls, piece):
        return cls(
            name=piece.name,
            ctl_ref=piece.ctl,
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, name, ctl_ref, fn, service_params, want_config):
        super().__init__(name, ctl_ref, fn, service_params, want_config)
        if not inspect.isgeneratorfunction(fn):
            raise RuntimeError(f"Function {fn!r} expected to be a generator function")

    def __repr__(self):
        return f"<FinalizerGenServiceTemplate {self.service_name}: {self._fn} {self._service_params} {self._want_config}>"

    @property
    def piece(self):
        return htypes.system.finalizer_gen_service_template(
            name=self.service_name,
            ctl=self._ctl_ref,
            function=pyobj_creg.actor_to_ref(self._fn),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )

    def resolve(self, system, service_name):
        service_args = self._resolve_service_args(system)
        gen = self._fn(*service_args)
        service = next(gen)
        system.add_finalizer(self.service_name, partial(self._finalize, gen))
        return service

    def _finalize(self, gen):
        try:
            next(gen)
        except StopIteration:
            pass
        else:
            raise RuntimeError(f"Generator function {self._fn!r} should have only one 'yield' statement")


class ActorTemplate:

    @classmethod
    def from_piece(cls, piece):
        return cls(
            t=pyobj_creg.invite(piece.t),
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            )

    def __init__(self, t, fn, service_params):
        self.t = t
        self._fn = fn
        self._service_params = service_params

    def __repr__(self):
        return f"<ActorTemplate {self._fn}({self._service_params})>"

    @property
    def piece(self):
        return htypes.system.actor_template(
            t=pyobj_creg.actor_to_ref(self.t),
            function=pyobj_creg.actor_to_ref(self._fn),
            service_params=tuple(self._service_params),
            )

    @property
    def key(self):
        return self.t

    def resolve(self, system, service_name):
        return self._resolve_services(self._fn, system)

    def _resolve_services(self, fn, system):
        return system.bind_services(fn, self._service_params, requester=ActorRequester(self.t))


class System:

    _system_name = "System"

    def __init__(self):
        self._name_to_layer = {}  # layer name -> layer.
        self._config_templates_cache = None
        self._name_to_service = {}
        self._resolve_stack = {}  # service name -> requester
        self._finalizers = {}  # service name -> fn
        self._init()

    def _init(self):
        config_ctl_creg_config = self._make_config_ctl_creg_config()
        self._config_ctl_creg = code_registry_ctr('config_ctl_creg', config_ctl_creg_config)
        # cfg_item_creg is used by DictConfigCtl.
        self._cfg_item_creg = cached_code_registry_ctr('cfg_item_creg', self._make_cfg_item_creg_config())
        config_ctl_creg_config[htypes.system.dict_config_ctl] = partial(DictConfigCtl.from_piece, cfg_item_creg=self._cfg_item_creg)
        self._dict_config_ctl = DictConfigCtl(self._cfg_item_creg)
        self._config_ctl = self._make_config_ctl({
            'system': self._dict_config_ctl,
            'config_ctl_creg': self._dict_config_ctl,
            'cfg_item_creg': self._dict_config_ctl,
            })
        self.add_core_service('cfg_item_creg', self._cfg_item_creg)
        self.add_core_service('config_ctl_creg', self._config_ctl_creg)
        self.add_core_service('config_ctl', self._config_ctl)
        self.add_core_service('get_layer_config_templates', self.get_layer_config_templates)
        self.add_core_service('get_system_config_piece', self.get_config_piece)
        self.add_core_service('system', self)

    def _make_config_ctl_creg_config(self):
        return {}

    def _make_config_ctl(self, config):
        return config

    def _make_cfg_item_creg_config(self):
        return {
            htypes.system.service_template: ServiceTemplate.from_piece,
            htypes.system.finalizer_gen_service_template: FinalizerGenServiceTemplate.from_piece,
            htypes.system.actor_template: ActorTemplate.from_piece,
            }

    @property
    def name_to_layer(self):
        return self._name_to_layer

    @property
    def service_names(self):
        return {*self._name_to_template, *self._name_to_service}

    def add_core_service(self, name, service):
        self._name_to_service[name] = service
        self._config_ctl[name] = self._dict_config_ctl

    def update_service_config(self, service_name, config):
        try:
            dest = self._config_templates[service_name]
        except KeyError:
            ctl = self._config_ctl[service_name]
            dest = ctl.empty_config_template()
            self._config_templates[service_name]= dest
        dest.update(config)

    def update_service_own_config(self, service_name, config):
        service = self._name_to_service[service_name]
        for key, template in config.items():
            value = template.resolve(self, service_name)
            service.update_config({key: value})

    def update_config_ctl(self, config):
        for service_name, template in config.items():
            self._config_ctl[service_name] = self._config_ctl_creg.invite(template.ctl_ref)

    def load_config(self, config_piece):
        layer = StaticConfigLayer(self, self['config_ctl'], config_piece)
        self.load_config_layer('full', layer)

    def load_config_layer(self, layer_name, layer):
        # layer.config is expected to be ordered with service_config_order.
        log.debug("Load config layer: %r; services: %s", layer_name, list(layer.config))
        self._name_to_layer[layer_name] = layer
        self.invalidate_config_cache()

    def service_config_order(self, service_name):
        order = {
            'cfg_item_creg': 1,
            'config_ctl_creg': 2,
            'system': 3,
            }
        return order.get(service_name, 10)

    @property
    def default_layer(self):
        return list(self._name_to_layer.values())[-1]

    def get_layer_config_templates(self, layer_name):
        layer = self._name_to_layer[layer_name]
        return self._collect_layers_configs([layer])

    def get_config_piece(self):
        return self.config_to_data(self._config_templates)

    def config_to_data(self, service_to_config):
        service_to_config_piece = {}
        for service_name, config in service_to_config.items():
            ctl = self._config_ctl[service_name]
            service_to_config_piece[service_name] = ctl.to_data(config)
        return service_pieces_to_config(service_to_config_piece)
        
    def get_config_template(self, service_name):
        try:
            return self._config_templates[service_name]
        except KeyError:
            ctl = self._config_ctl[service_name]
            return ctl.empty_config_template()

    def invalidate_config_cache(self):
        self._config_templates_cache = None

    def _collect_layers_configs(self, layer_list):
        service_to_config = dict()
        for layer in layer_list:
            for service_name, config in layer.config.items():
                ctl = self._config_ctl[service_name]
                try:
                    dest = service_to_config[service_name]
                except KeyError:
                    dest = ctl.empty_config_template()
                    service_to_config[service_name] = dest
                ctl.merge(dest, config)
        return service_to_config

    @property
    def _config_templates(self):
        if self._config_templates_cache is not None:
            return self._config_templates_cache
        service_to_config = self._collect_layers_configs(self._name_to_layer.values())
        self._config_templates_cache = service_to_config
        return service_to_config

    @property
    def _name_to_template(self):
        return self._config_templates.get('system', {})

    def run(self, root_name, *args, **kw):
        service = self.resolve_service(root_name)
        log.info("%s: run root service %s: %s", self._system_name, root_name, service)
        try:
            return self._run_service(service, args, kw)
        finally:
            self.close()
            log.info("%s: stopped", self._system_name)

    def _run_service(self, service, args, kw):
        return service(*args, **kw)

    def resolve_config(self, service_name):
        config_template = self.get_config_template(service_name)
        ctl = self._config_ctl[service_name]
        return ctl.resolve(self, service_name, config_template)

    def __getitem__(self, service_name):
        return self.resolve_service(service_name)

    def resolve_service(self, name, requester=None):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        # ConfigItemMissing(KeyError) can be fired here, should be out of try/except KeyError.
        name_to_template = self._name_to_template
        try:
            template = name_to_template[name]
        except KeyError:
            self._raise_missing_service(name)
        if name in self._resolve_stack:
            self._raise_service_loop(name, requester)
        self._resolve_stack[name] = requester
        try:
            service = template.resolve(self, name)
        finally:
            self._resolve_stack.popitem()
        self._name_to_service[name] = service
        return service

    def bind_services(self, fn, params, requester=None):
        service_kw = {
            name: self.resolve_service(name, requester)
            for name in params
            }
        return partial(fn, **service_kw)

    def _raise_service_loop(self, name, requester):
        stack = [
            *self._resolve_stack.items(),
            (name, requester),
            ]
        svc_list = [
            f"{req} -> {name}" if req else name
            for name, req in stack
            ]
        loop = " -> ".join(svc_list)
        raise ServiceDepLoopError(f"Service dependency loop: {loop}")

    def add_finalizer(self, service_name, finalizer):
        self._finalizers[service_name] = finalizer

    def close(self):
        log.info("%s: run %d finalizers:", self._system_name, len(self._finalizers))
        for name, fn in reversed(self._finalizers.items()):
            log.info("%s: call finalizer for %r: %s", self._system_name, name, fn)
            fn()

    def _raise_missing_service(self, service_name):
        raise UnknownServiceError(service_name)


def run_config(config, root_name, *args, **kw):
    system = System()
    system.load_config(config)
    system.run(root_name, *args, **kw)


def run_projects(projects, root_name, *args, **kw):
    system = System()
    for project in projects:
        layer = ProjectConfigLayer(system, system['config_ctl'], project)
        system.load_config_layer(project.name, layer)
    system.run(root_name, *args, **kw)
