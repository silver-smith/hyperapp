import asyncio
import inspect
import logging
import weakref
from collections import defaultdict
from functools import partial

from hyperapp.common.config_item_missing import ConfigItemMissingError

from .services import (
    pyobj_creg,
    )
from .code.system import UnknownServiceError, System
from .code.service_req import ServiceReq
from .code.actor_req import ActorReq

log = logging.getLogger(__name__)


def have_running_loop():
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def service_finalize(fn, gen):
    try:
        next(gen)
    except StopIteration:
        pass
    else:
        raise RuntimeError(f"Generator function {fn!r} should have only one 'yield' statement")


def service_async_finalize(system, fn, gen):
    try:
        system.run_async_coroutine(anext(gen))
    except StopAsyncIteration:
        pass
    else:
        raise RuntimeError(f"Async generator function {fn!r} should have only one 'yield' statement")


def check_no_running_loop(fn):
    if have_running_loop():
        raise RuntimeError(f"Use mark.fixture.obj for async fixtures used inside async tests or fixtures: {fn}")


def resolve_service_fn(system, service_name, fn, fn_params, service_params, args, kw):
    free_params_ofs = len(service_params)
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
        config_args = [system.resolve_config(service_name)]
        free_params_ofs += 1
    free_params = fn_params[free_params_ofs:]
    service_args = [
        system.resolve_service(name)
        for name in service_params
        ]
    service = fn(*config_args, *service_args, *args, **kw)
    if inspect.isgeneratorfunction(fn) and not free_params:
        gen = service
        service = next(gen)
        system.add_finalizer(service_name, partial(service_finalize, fn, gen))
        is_gen = True
    else:
        is_gen = False
    if inspect.isasyncgenfunction(fn):
        gen = service
        check_no_running_loop(fn)
        service = system.run_async_coroutine(anext(gen))
        system.add_finalizer(service_name, partial(service_async_finalize, system, fn, gen))
    return (want_config, service_params, free_params, is_gen, service)


class ServiceConfigProbe:

    def __init__(self, builtin_config):
        self._builtin_config = builtin_config
        self._config = {**builtin_config}
        self._used_services = set()

    def __getitem__(self, service_name):
        try:
            service = self._config[service_name]
        except KeyError:
            raise UnknownServiceError(service_name)
        else:
            if service_name not in self._builtin_config:
                self._used_services.add(service_name)
            return service

    def __setitem__(self, key, value):
        self._config[key] = value

    @property
    def used_services(self):
        return self._used_services


class ConfigProbe:

    def __init__(self, service_name, config):
        self._service_name = service_name
        self._config = config
        self._used_keys = set()

    def __getitem__(self, key):
        try:
            value = self._config[key]
        except KeyError:
            raise ConfigItemMissingError(self._service_name, key)
        else:
            if not self._is_builtin_key(key):
                self._used_keys.add(key)
            return value

    def __iter__(self):
        return iter(self._config)

    def __setitem__(self, key, value):
        self._config[key] = value

    def get(self, key, default=None):
        value = self._config.get(key, default)
        if value is not default and not self._is_builtin_key(key):
            self._used_keys.add(key)
        return value

    def items(self):
        return self._config.items()

    def update(self, config):
        self._config.update(config)

    @property
    def used_keys(self):
        return self._used_keys

    def _is_builtin_key(self, key):
        return False


# Config probe for services having builtin config elements.
class SystemConfigProbe(ConfigProbe):

    def __init__(self, service_name, builtin_config, config):
        full_config = {**builtin_config, **config}
        super().__init__(service_name, full_config)
        self._builtin_config = builtin_config

    def update_builtin_config(self, key, value):
        self._builtin_config[key] = value
        self._config[key] = value

    def _is_builtin_key(self, key):
        return key in self._builtin_config


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
        return fn(*service_args)


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
        self._apply_obj(service_params=[])

    def __eq__(self, rhs):
        service = self._apply_obj(self._params)
        return service == rhs

    def __hash__(self):
        service = self._apply_obj(self._params)
        return hash(service)

    def __bool__(self):
        service = self._apply_obj(self._params)
        return bool(service)

    def __call__(self, *args, **kw):
        free_param_count = len(args) + len(kw)
        if free_param_count:
            service_params = self._params[:-free_param_count]
        else:
            service_params = self._params
        return self._apply(service_params, *args, **kw)

    def __getattr__(self, name):
        try:
            service = self._apply_obj(self._params)
        except AttributeError as x:
            # Do not let it out - caller will treat this as just a missing attribute.
            raise RuntimeError(f"Error resolving service or fixture: {x}") from x
        return getattr(service, name)

    def __getitem__(self, key):
        service = self._apply_obj(self._params)
        return service[key]

    def __setitem__(self, key, value):
        service = self._apply_obj(self._params)
        service[key] = value

    def __iter__(self):
        service = self._apply_obj(self._params)
        return iter(service)

    def _apply(self, service_params, *args, **kw):
        if self._resolved:
            return self._service
        want_config, service_params, free_params, is_gen, service = resolve_service_fn(
            self._system, self._name, self._fn, self._params, service_params, args, kw)
        self._service = service
        self._add_service_constructor(want_config, service_params, is_gen)
        self._resolved = True
        return service

    def _apply_obj(self, service_params, *args, **kw):
        service = self._apply(service_params, *args, **kw)
        if inspect.iscoroutine(service):
            check_no_running_loop(self._fn)
            service = self._system.run_async_coroutine(service)
            self._service = service
        return service

    def _add_service_constructor(self, want_config, template, is_gen):
        pass


class SystemProbe(System):

    _system_name = "System probe"
    _globals = weakref.WeakSet()

    def __init__(self):
        super().__init__()
        self._config_fixtures = defaultdict(list)  # service_name -> fixture list
        self._async_error = None  # (error message, exception) tuple
        self._service_probes = []
        self._service_to_config_probe = {}
        self._init_probe()

    # Do not _init before our own attributes are initialized.
    def _init(self):
        pass

    def _init_probe(self):
        super()._init()

    def _make_config_probe(self, service_name, config):
        probe = ConfigProbe(service_name, config)
        self._service_to_config_probe[service_name] = probe
        return probe

    def _make_system_config_probe(self, service_name, builtin_config, config):
        probe = SystemConfigProbe(service_name, builtin_config, config)
        self._service_to_config_probe[service_name] = probe
        return probe

    def _make_config_ctl_creg_config(self):
        return self._make_system_config_probe(
            'config_ctl_creg', builtin_config={}, config={})

    def _make_config_ctl(self, config):
        probe = ServiceConfigProbe(config)
        self._service_probes.append(probe)
        return probe

    def _make_cfg_item_creg_config(self):
        builtin_config = super()._make_cfg_item_creg_config()
        return self._make_system_config_probe('cfg_item_creg', builtin_config, config={})

    def _update_builtin_config(self, config, key, value):
        config.update_builtin_config(key, value)

    def add_item_fixtures(self, service_name, fixture_list):
        self._config_fixtures[service_name] += fixture_list

    def add_global(self, global_obj):
        self._globals.add(global_obj)

    def _run_service(self, service, args, kw):
        value = super()._run_service(service, args, kw)
        if inspect.iscoroutine(value):
            return self.run_async_coroutine(value)
        return value

    def resolve_config(self, service_name):
        ctl = self._config_ctl[service_name]
        config = super().resolve_config(service_name)
        for fixture in self._config_fixtures.get(service_name, []):
            fixture_cfg = fixture.resolve(self)
            ctl.merge(config, fixture_cfg)
        return self._make_config_probe(service_name, config)

    def add_constructor(self, ctr):
        ctr_collector = self.resolve_service('ctr_collector')
        ctr_collector.add_constructor(ctr)

    def migrate_globals(self):
        for obj in self._globals:
            obj.migrate_to(self)

    def run_async_coroutine(self, coroutine):
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

    def enum_used_requirements(self):
        for probe in self._service_probes:
            for service_name in probe.used_services:
                yield ServiceReq(service_name)
        for service_name, probe in self._service_to_config_probe.items():
            for key in probe.used_keys:
                yield ActorReq(service_name, t=key)
