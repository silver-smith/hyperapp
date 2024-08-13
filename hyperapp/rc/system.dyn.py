import inspect
from collections import defaultdict
from functools import partial

from . import htypes
from .services import (
    pyobj_creg,
    code_registry_ctr2,
    )


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


class ServiceTemplateBase:

    def __init__(self, name, fn, service_params, want_config):
        self.service_name = name
        self._fn = fn
        self._service_params = service_params
        self._want_config = want_config

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
            fn=pyobj_creg.invite(piece.function),
            free_params=piece.free_params,
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, name, fn, free_params, service_params, want_config):
        super().__init__(name, fn, service_params, want_config)
        self._free_params = free_params

    def __repr__(self):
        return f"<ServiceTemplate {self.service_name}: {self._fn} {self._free_params} {self._service_params} {self._want_config}>"

    @property
    def piece(self):
        return htypes.system.service_template(
            name=self.service_name,
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
            fn=pyobj_creg.invite(piece.function),
            service_params=piece.service_params,
            want_config=piece.want_config,
            )

    def __init__(self, name, fn, service_params, want_config):
        super().__init__(name, fn, service_params, want_config)
        if not inspect.isgeneratorfunction(fn):
            raise RuntimeError(f"Function {fn!r} expected to be a generator function")

    def __repr__(self):
        return f"<FinalizerGenServiceTemplate {self.service_name}: {self._fn} {self._service_params} {self._want_config}>"

    @property
    def piece(self):
        return htypes.system.finalizer_gen_service_template(
            name=self.service_name,
            function=pyobj_creg.actor_to_ref(self._fn),
            service_params=tuple(self._service_params),
            want_config=self._want_config,
            )

    def resolve(self, system, service_name):
        service_args = self._resolve_service_args(system)
        gen = self._fn(*service_args)
        service = next(gen)
        system.add_finalizer(partial(self._finalize, gen))
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

    def resolve(self, system, service_name):
        if not self._service_params:
            return self._fn
        service_kw = {
            name: system.resolve_service(name)
            for name in self._service_params
            }
        return partial(self._fn, **service_kw)

        
class ServiceTemplateCfg:

    @classmethod
    def from_piece(cls, piece, service_name):
        template = ServiceTemplate.from_piece(piece)
        return cls(template)

    def __init__(self, template):
        self.key = template.service_name
        self.value = template

    @property
    def piece(self):
        return self.value.piece


class FinalizerGenServiceTemplateCfg:

    @classmethod
    def from_piece(cls, piece, service_name):
        template = FinalizerGenServiceTemplate.from_piece(piece)
        return cls(template)

    def __init__(self, template):
        self.key = template.service_name
        self.value = template

    @property
    def piece(self):
        return self.value.piece


class ActorTemplateCfg:

    @classmethod
    def from_piece(cls, piece, service_name):
        template = ActorTemplate.from_piece(piece)
        return cls(template)

    def __init__(self, template):
        self.key = template.t
        self.value = template

    @property
    def piece(self):
        return self.value.piece


class System:

    def __init__(self):
        self._configs = defaultdict(dict)
        self._name_to_template = self._configs['system']
        self._name_to_service = {}
        self._finalizers = []

    def add_core_service(self, name, service):
        self._name_to_service[name] = service

    def update_config(self, service_name, config):
        self._configs[service_name].update(config)

    def load_config(self, config_piece):
        cfg_item_creg_config = {
            htypes.system.service_template: ServiceTemplateCfg.from_piece,
            htypes.system.finalizer_gen_service_template: FinalizerGenServiceTemplateCfg.from_piece,
            htypes.system.actor_template: ActorTemplateCfg.from_piece,
            }
        cfg_item_creg = code_registry_ctr2('cfg-item', cfg_item_creg_config)
        self.add_core_service('system_config', config_piece)
        self.add_core_service('cfg_item_creg', cfg_item_creg)
        for sc in config_piece.services:
            for item_ref in sc.items:
                item = cfg_item_creg.invite(item_ref, sc.service)
                self.update_config(sc.service, {item.key: item.value})

    def run(self, root_name, *args, **kw):
        service = self.resolve_service(root_name)
        try:
            return service(*args, **kw)
        finally:
            self._run_finalizers()

    def resolve_config(self, service_name):
        config = {}
        for key, template in self._configs.get(service_name, {}).items():
            config[key] = template.resolve(self, service_name)
        return config

    def resolve_service(self, name):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        try:
            template = self._name_to_template[name]
        except KeyError:
            self._raise_missing_service(name)
        service = template.resolve(self, name)
        self._name_to_service[name] = service
        return service

    def add_finalizer(self, finalizer):
        self._finalizers.append(finalizer)

    def _run_finalizers(self):
        for fn in reversed(self._finalizers):
            fn()

    def _raise_missing_service(self, service_name):
        raise UnknownServiceError(service_name)


def run_system(config, root_name, *args, **kw):
    system = System()
    system.load_config(config)
    system.run(root_name, *args, **kw)
