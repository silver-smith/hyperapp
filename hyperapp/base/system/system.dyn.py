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

log = logging.getLogger(__name__)


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


class ServiceDepLoopError(Exception):
    pass


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
            fn_ref=piece.function,
            service_params=piece.service_params,
            )

    def __init__(self, t, fn_ref, service_params):
        self.t = t
        self._fn_ref = fn_ref
        self._service_params = service_params

    @property
    def piece(self):
        return htypes.system.actor_template(
            t=pyobj_creg.actor_to_ref(self.t),
            function=self._fn_ref,
            service_params=tuple(self._service_params),
            )

    @property
    def key(self):
        return self.t

    def resolve(self, system, service_name):
        fn = pyobj_creg.invite(self._fn_ref)
        return self._resolve_services(fn, system)

    def _resolve_services(self, fn, system):
        if not self._service_params:
            return fn
        service_kw = {
            name: system.resolve_service(name, requester=ActorRequester(self.t))
            for name in self._service_params
            }
        return partial(fn, **service_kw)


class System:

    _system_name = "System"

    def __init__(self):
        self._layer_to_configs = {}  # layer_name -> service name -> service config
        self._configs_cache = None
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
        dict_config_ctl = DictConfigCtl(self._cfg_item_creg)
        self._config_ctl = self._make_config_ctl({
            'system': dict_config_ctl,
            'config_ctl_creg': dict_config_ctl,
            'cfg_item_creg': dict_config_ctl,
            'pyobj_creg': dict_config_ctl,
            })
        self.add_core_service('cfg_item_creg', self._cfg_item_creg)
        self.add_core_service('config_ctl_creg', self._config_ctl_creg)
        self.add_core_service('config_ctl', self._config_ctl)
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
    def service_names(self):
        return {*self._name_to_template, *self._name_to_service}

    def add_core_service(self, name, service):
        self._name_to_service[name] = service

    def update_config(self, layer_name, service_name, config):
        self._update_config(layer_name, service_name, config)
        self._update_system_config_piece()

    def _update_config(self, layer_name, service_name, config):
        self._configs_cache = None
        service_to_config = self._layer_to_configs.setdefault(layer_name, {})
        try:
            dest = service_to_config[service_name]
        except KeyError:
            service_to_config[service_name] = config
        else:
            try:
                ctl = self._config_ctl[service_name]
            except KeyError:
                self._raise_missing_service(service_name)
            ctl.merge(dest, config)
        if service_name in {'config_ctl_creg', 'cfg_item_creg'}:
            # Subsequent update_config calls may already use it.
            self._update_service_config(service_name, config)
        if service_name == 'system':
            # Subsequent update_config calls may already use it.
            self._update_config_ctl(config)

    def _update_service_config(self, service_name, config):
        service = self._name_to_service[service_name]
        for key, template in config.items():
            value = template.resolve(self, service_name)
            service.update_config({key: value})

    def _update_config_ctl(self, config):
        for service_name, template in config.items():
            self._config_ctl[service_name] = self._config_ctl_creg.invite(template.ctl_ref)

    def load_config(self, config_piece):
        self.load_config_layer('single', config_piece)

    def load_config_layer(self, layer_name, config_piece):
        service_to_config = {
            rec.service: web.summon(rec.config)
            for rec in config_piece.services
            }
        ordered_services = sorted(service_to_config, key=self._service_config_order)
        for service_name in ordered_services:
            config_piece = service_to_config.get(service_name)
            self._load_config_piece(layer_name, service_name, config_piece)
        self.add_core_service('layer_config_templates', self._layer_to_configs)
        self._update_system_config_piece()

    def _update_system_config_piece(self):
        config_piece = self.config_to_data(self._configs)
        self.add_core_service('system_config_piece', config_piece)

    def _service_config_order(self, service_name):
        order = {
            'cfg_item_creg': 1,
            'config_ctl_creg': 2,
            'system': 3,
            'pyobj_creg': 21,
            }
        return order.get(service_name, 10)

    def _load_config_piece(self, layer_name, service_name, config_piece):
        if not config_piece:
            return
        if service_name == 'pyobj_creg':
            self._load_pyobj_creg(config_piece)
            return
        ctl = self._config_ctl[service_name]
        config = ctl.from_data(config_piece)
        self._update_config(layer_name, service_name, config)

    # TODO: Think how to load pyobj_creg config not by system. It is a global registry.
    def _load_pyobj_creg(self, config_piece):
        if not config_piece:
            return
        ctl = self._config_ctl['pyobj_creg']
        config_template = ctl.from_data(config_piece)
        config = ctl.resolve(self, 'pyobj_creg', config_template)
        pyobj_creg.update_config(config)

    def config_to_data(self, service_to_config):
        service_to_config_piece = {}
        for service_name, config in service_to_config.items():
            ctl = self._config_ctl[service_name]
            service_to_config_piece[service_name] = ctl.to_data(config)
        return service_pieces_to_config(service_to_config_piece)
        
    @property
    def _configs(self):
        if self._configs_cache is not None:
            return self._configs_cache
        result = dict()
        for service_to_config in self._layer_to_configs.values():
            for service_name, config in service_to_config.items():
                ctl = self._config_ctl[service_name]
                try:
                    dest = result[service_name]
                except KeyError:
                    dest = ctl.empty_config_template()
                    result[service_name] = dest
                ctl.merge(dest, config)
        self._configs_cache = result
        return result

    @property
    def _name_to_template(self):
        return self._configs.get('system', {})

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
        ctl = self._config_ctl[service_name]
        config_template = self._configs.get(service_name, {})
        try:
            return ctl.resolve(self, service_name, config_template)
        except ServiceDepLoopError:
            return ctl.lazy_config(self, service_name, config_template)

    def __getitem__(self, service_name):
        return self.resolve_service(service_name)

    def resolve_service(self, name, requester=None):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        try:
            template = self._name_to_template[name]
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
        system.load_config_layer(project.name, project.config)
    system.run(root_name, *args, **kw)
