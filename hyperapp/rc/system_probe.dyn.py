import asyncio
import inspect
import logging
import weakref
from collections import defaultdict
from functools import partial

from .services import pyobj_creg
from .code.system import System

log = logging.getLogger(__name__)


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


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


def resolve_service(system, service_name, fn, service_params, args, kw):
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
    service_args = [
        system.resolve_service(name)
        for name in service_params
        ]
    service = fn(*config_args, *service_args, *args, **kw)
    if inspect.isgeneratorfunction(fn):
        gen = service
        service = next(gen)
        system.add_finalizer(service_name, partial(service_finalize, fn, gen))
    if inspect.isasyncgenfunction(fn):
        gen = service
        check_no_running_loop(fn)
        service = system.run_async_coroutine(anext(gen))
        system.add_finalizer(service_name, partial(service_async_finalize, system, fn, gen))
    return (want_config, service_params, service)


class FixtureObjTemplate:

    def __init__(self, ctl_ref, fn_piece, params):
        self._ctl_ref = ctl_ref
        self._fn = fn_piece
        self._params = params

    def __repr__(self):
        return f"<FixtureObjTemplate {self._fn} {self._params}>"

    @property
    def ctl_ref(self):
        return self._ctl_ref

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        want_config, service_params, service = resolve_service(
            system, service_name, fn, self._params, args=[], kw={})
        if inspect.iscoroutine(service):
            service = system.run_async_coroutine(service)
        return service


class FixtureProbeTemplate:

    def __init__(self, ctl_ref, fn_piece, params):
        self._ctl_ref = ctl_ref
        self._fn = fn_piece
        self._params = params

    def __repr__(self):
        return f"<FixtureProbeTemplate {self._fn} {self._params}>"

    @property
    def ctl_ref(self):
        return self._ctl_ref

    def resolve(self, system, service_name):
        fn = pyobj_creg.animate(self._fn)
        probe = FixtureProbe(system, service_name, self._ctl_ref, fn, self._params)
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

    def __iter__(self):
        return iter(self._config)

    def __setitem__(self, key, value):
        self._config[key] = value

    def get(self, key, default=None):
        return self._config.get(key, default)

    def items(self):
        return self._config.items()

    def update(self, config):
        self._config.update(config)


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

    def __call__(self, *args, **kw):
        free_param_count = len(args) + len(kw)
        if free_param_count:
            service_params = self._params[:-free_param_count]
        else:
            service_params = self._params
        return self._apply(service_params, *args, **kw)

    def __getattr__(self, name):
        service = self._apply_obj(self._params)
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
        want_config, service_params, service = resolve_service(self._system, self._name, self._fn, service_params, args, kw)
        self._service = service
        self._add_constructor(want_config, service_params)
        self._resolved = True
        return service

    def _apply_obj(self, service_params, *args, **kw):
        service = self._apply(service_params, *args, **kw)
        if inspect.iscoroutine(service):
            check_no_running_loop(self._fn)
            service = self._system.run_async_coroutine(service)
            self._service = service
        return service

    def _add_constructor(self, want_config, template):
        pass


class FixtureProbe(Probe):

    def __init__(self, system_probe, service_name, ctl_ref, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._ctl_ref = ctl_ref

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params} {self._ctl_ref}>"


class SystemProbe(System):

    _system_name = "System probe"
    _globals = weakref.WeakSet()

    def __init__(self):
        super().__init__()
        self._config_fixtures = defaultdict(list)  # service_name -> fixture list
        self._async_error = None  # (error message, exception) tuple

    def _make_config_ctl_creg_config(self):
        return ConfigProbe('config_ctl_creg', {})

    def _make_cfg_item_creg_config(self):
        return ConfigProbe('cfg_item_creg', super()._make_cfg_item_creg_config())

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
        return ConfigProbe(service_name, config)

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
