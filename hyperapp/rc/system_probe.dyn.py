import asyncio
import inspect
import logging
import weakref
from collections import defaultdict
from dataclasses import dataclass
from functools import partial
from typing import Any

from .services import pyobj_creg
from .code.system import System

log = logging.getLogger(__name__)


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


@dataclass
class ServiceTemplateRec:

    attr_name: str
    ctl: Any
    free_params: list[str]
    service_params: list[str]
    want_config: bool


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
        fn = pyobj_creg.animate(self._fn)
        probe = ServiceProbe(system, self._attr_name, service_name, self._ctl, fn, self._params)
        probe.apply_if_no_params()
        return probe


class ActorProbeTemplate:

    def __init__(self, module_name, attr_qual_name, service_name, t, fn_piece, params):
        self._module_name = module_name
        self._attr_qual_name = attr_qual_name
        self._service_name = service_name
        self._t = t
        self._fn = fn_piece
        self._params = params

    def __repr__(self):
        return f"<ActorProbeTemplate {self._module_name}/{self._attr_qual_name}/{self._t}: {self._fn} {self._params}>"

    def resolve(self, system, service_name):
        return pyobj_creg.animate(self._fn)


class FixtureProbeTemplate:

    def __init__(self, ctl, fn_piece, params):
        self._ctl = ctl
        self._fn = fn_piece
        self._params = params

    def __repr__(self):
        return f"<FixtureProbeTemplate {self._fn} {self._params}>"

    @property
    def ctl(self):
        return self._ctl

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        probe = FixtureProbe(system, service_name, self._ctl, fn, self._params)
        probe.apply_if_no_params()
        return probe


class ConfigItemRequiredError(Exception):

    def __init__(self, service_name, key):
        super().__init__(f"Configuration item is required for {service_name}: {key}")
        self.service_name = service_name
        self.key = key


class ConfigProbe:

    def __init__(self, service_name, config):
        self._service_name = service_name
        self._config = config

    def __getitem__(self, key):
        try:
            return self._config[key]
        except KeyError:
            raise ConfigItemRequiredError(self._service_name, key)

    def items(self):
        return self._config.items()


class ConfigFixture:

    def __init__(self, fn_piece, service_params):
        self._fn = fn_piece
        self._service_params = service_params

    def __repr__(self):
        return f"<ConfigFixture {self._fn} {self._service_params}>"

    def resolve(self, system):
        fn = pyobj_creg.animate(self._fn)
        service_args = [
            system.resolve_service(name)
            for name in self._service_params
            ]
        config = fn(*service_args)
        if not isinstance(config, dict):
            raise RuntimeError(f"Config item fixture should return a key->value dict ({fn}): {config!r}")
        return config


class Probe:

    def __init__(self, system_probe, service_name, fn, params):
        self._system = system_probe
        self._name = service_name
        self._fn = fn
        self._params = params
        self._resolved = False
        self._service = None

    def apply_if_no_params(self):
        if self._params:
            return
        self._apply(service_params=[])

    def __call__(self, *args, **kw):
        free_param_count = len(args) + len(kw)
        if free_param_count:
            service_params = self._params[:-free_param_count]
        else:
            service_params = self._params
        return self._apply(service_params, *args, **kw)

    def __getattr__(self, name):
        service = self._apply(self._params)
        return getattr(service, name)

    def __getitem__(self, key):
        service = self._apply(self._params)
        return service[key]

    def __setitem__(self, key, value):
        service = self._apply(self._params)
        service[key] = value

    def __iter__(self):
        service = self._apply(self._params)
        return iter(service)

    def _apply(self, service_params, *args, **kw):
        if self._resolved:
            return self._service
        try:
            idx = service_params.index('config')
        except ValueError:
            want_config = False
            config_args = []
        else:
            if idx != 0:
                raise RuntimeError("'config' should be first parameter")
            service_params = service_params[1:]
            want_config = True
            config_args = [self._system.resolve_config(self._name)]
        service_args = [
            self._system.resolve_service(name)
            for name in service_params
            ]
        service = self._fn(*config_args, *service_args, *args, **kw)
        if inspect.isgeneratorfunction(self._fn):
            gen = service
            service = next(gen)
            self._system.add_finalizer(self._name, partial(self._finalize, gen))
        self._service = service
        self._add_resolved_template(want_config, service_params)
        self._resolved = True
        return service

    def _finalize(self, gen):
        try:
            next(gen)
        except StopIteration:
            pass
        else:
            raise RuntimeError(f"Generator function {self._fn!r} should have only one 'yield' statement")

    def _add_resolved_template(self, want_config, template):
        pass


class ServiceProbe(Probe):

    def __init__(self, system_probe, attr_name, service_name, ctl, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._attr_name = attr_name
        self._ctl = ctl

    def __repr__(self):
        return f"<ServiceProbe {self._attr_name} {self._fn} {self._params} {self._ctl}>"

    def _add_resolved_template(self, want_config, service_params):
        free_params_ofs = len(service_params)
        if want_config:
            free_params_ofs += 1
        template = ServiceTemplateRec(
            attr_name=self._attr_name,
            ctl=self._ctl,
            free_params=self._params[free_params_ofs:],
            service_params=service_params,
            want_config=want_config,
            )
        self._system.add_resolved_template(self._name, template)


class FixtureProbe(Probe):

    def __init__(self, system_probe, service_name, ctl, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._ctl = ctl

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params} {self._ctl}>"


class SystemProbe(System):

    _system_name = "System probe"
    _globals = weakref.WeakSet()

    def __init__(self):
        super().__init__()
        self._config_fixtures = defaultdict(list)  # service_name -> fixture list
        self._resolved_templates = {}
        self._async_error = None  # (error message, exception) tuple

    def add_item_fixtures(self, service_name, fixture_list):
        self._config_fixtures[service_name] += fixture_list

    def add_global(self, global_obj):
        self._globals.add(global_obj)

    def _run_service(self, service, args, kw):
        value = super()._run_service(service, args, kw)
        if inspect.iscoroutine(value):
            self._run_async_coroutine(value)

    @property
    def resolved_templates(self):
        return self._resolved_templates

    def resolve_config(self, service_name):
        config = super().resolve_config(service_name)
        for fixture in self._config_fixtures.get(service_name, []):
            cfg = fixture.resolve(self)
            config.update(cfg)
        return ConfigProbe(service_name, config)

    def add_resolved_template(self, name, service):
        self._resolved_templates[name] = service

    def migrate_globals(self):
        for obj in self._globals:
            obj.migrate_to(self)

    def _run_async_coroutine(self, coroutine):
        runner = asyncio.Runner()
        loop = runner.get_loop()
        prev_handler = loop.get_exception_handler()
        loop.set_exception_handler(self._asyncio_exception_handler)
        try:
            log.info("Running coroutine: %r", coroutine)
            return runner.run(coroutine)
        except TimeoutError:
            self._check_async_error()
        finally:
            loop.set_exception_handler(prev_handler)
        self._check_async_error()

    def _check_async_error(self):
        if not self._async_error:
            return
        error, origin = self._async_error
        raise RuntimeError(f"{error}: {origin.__class__.__name__}: {origin}") from origin

    def _asyncio_exception_handler(self, loop, context):
        self._async_error = (context['message'], context['exception'])
