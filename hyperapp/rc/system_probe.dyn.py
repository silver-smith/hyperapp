import asyncio
import inspect
import logging
import weakref
from collections import defaultdict
from enum import Enum
from functools import partial

from hyperapp.boot.config_key_error import ConfigKeyError

from .services import (
    pyobj_creg,
    )
from .code.system import UnknownServiceError, System
from .code.probe import ProbeBase
from .code.marker_utils import split_service_params

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


class ServiceConfigProbe:

    def __init__(self, config, used_keys):
        self._config = {**config}
        self._used_keys = used_keys

    def __getitem__(self, service_name):
        try:
            service = self._config[service_name]
        except KeyError:
            raise UnknownServiceError(service_name)
        self._used_keys.add(('system', service_name))
        return service

    def __setitem__(self, key, value):
        self._config[key] = value


class ConfigProbe:

    def __init__(self, service_name, config, used_keys):
        self._service_name = service_name
        self._config = config
        self._used_keys = used_keys

    def __contains__(self, key):
        result = key in self._config
        if result:
            self._used_keys.add((self._service_name, key))
        return result

    def __getitem__(self, key):
        try:
            value = self._config[key]
        except ConfigKeyError:
            raise
        except KeyError:
            if isinstance(key, Probe):
                key = key.apply_obj()
            raise ConfigKeyError(self._service_name, key)
        self._used_keys.add((self._service_name, key))
        return value

    def __iter__(self):
        return iter(self._config)

    def __setitem__(self, key, value):
        self._config[key] = value

    def get(self, key, default=None):
        value = self._config.get(key, default)
        self._used_keys.add((self._service_name, key))
        return value

    def items(self):
        return self._config.items()

    def values(self):
        return self._config.values()

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

    class _Kind(Enum):
        function = 'function'
        object = 'object'

    def __init__(self, system_probe, service_name, fn, params):
        self._system = system_probe
        self._name = service_name
        self._fn = fn
        self._params = params
        self._resolved = False
        self._service = None
        self._service_kind = None 

    def apply_if_no_params(self):
        if self._params:
            return
        self._apply()

    def apply_obj(self):
        return self._apply()

    def __eq__(self, rhs):
        service = self.apply_obj()
        return service == rhs

    def __hash__(self):
        service = self.apply_obj()
        return hash(service)

    def __bool__(self):
        service = self.apply_obj()
        return bool(service)

    def __call__(self, *args, **kw):
        return self._apply(*args, **kw)

    def __getattr__(self, name):
        try:
            service = self.apply_obj()
        except AttributeError as x:
            # Do not let it out - caller will treat this as just a missing attribute.
            raise RuntimeError(f"Error resolving service or fixture: {x}") from x
        return getattr(service, name)

    def __getitem__(self, key):
        service = self.apply_obj()
        return service[key]

    def __setitem__(self, key, value):
        service = self.apply_obj()
        service[key] = value

    def __delitem__(self, key):
        service = self.apply_obj()
        del service[key]

    def __iter__(self):
        service = self.apply_obj()
        return iter(service)

    def __truediv__(self, other):
        service = self.apply_obj()
        return service / other

    def _apply(self, *args, **kw):
        if self._resolved:
            if self._service_kind == self._Kind.object:
                return self._service
            else:
                return self._service(*args, **kw)
        params = split_service_params(self._fn, args, kw)
        service_args, result = self._resolve_service(params, args, kw)
        if params.free_names:
            self._service = partial(self._fn, *service_args)
            self._service_kind = self._Kind.function
            is_gen = False
        else:
            is_gen, result = self._resolve_result(result)
            self._service = result
            self._service_kind = self._Kind.object
        self._add_service_constructor(params, is_gen)
        self._resolved = True
        return result

    def _resolve_service(self, params, args, kw):
        if params.has_config:
            config_args = [self._system.resolve_config(self._name)]
        else:
            config_args = []
        service_args = [
            self._system.resolve_service(name)
            for name in params.service_names
            ]
        result = self._fn(*config_args, *service_args, *args, **kw)
        return ([*config_args, *service_args], result)

    def _resolve_result(self, result):
        if inspect.isgeneratorfunction(self._fn):
            gen = result
            result = next(gen)
            self._system.add_finalizer(self._name, partial(service_finalize, self._fn, gen))
            return (True, result)
        if inspect.isasyncgenfunction(self._fn):
            gen = result
            result = self._run_coro(anext(gen))
            is_gen = True
            self._system.add_finalizer(self._name, partial(service_async_finalize, self._system, self._fn, gen))
            return (True, result)
        if inspect.iscoroutine(result):
            result = self._run_coro(result)
        return (False, result)

    def _run_coro(self, coro):
        self._check_no_running_loop()
        return self._system.run_async_coroutine(coro)

    def _check_no_running_loop(self):
        if have_running_loop():
            raise RuntimeError(f"Use mark.fixture.obj for async fixtures used inside async tests or fixtures: {self._fn}")

    def _add_service_constructor(self, params, is_gen):
        pass


class SystemProbe(System):

    _system_name = "System probe"
    _globals = weakref.WeakSet()

    def __init__(self):
        super().__init__()
        self._config_fixtures = defaultdict(list)  # service_name -> fixture list
        self._async_error = None  # (error message, exception) tuple
        self._used_keys = set()  # (service, key) set
        self._init_probe()

    # Do not _init before our own attributes are initialized.
    def _init(self):
        pass

    def _init_probe(self):
        super()._init()

    def _make_config_probe(self, service_name, config):
        return ConfigProbe(service_name, config, self._used_keys)

    def _make_config_ctl_creg_config(self):
        return self._make_config_probe('config_ctl_creg', config={})

    def _make_config_ctl(self, config):
        return ServiceConfigProbe(config, self._used_keys)

    def _make_cfg_item_creg_config(self):
        config = super()._make_cfg_item_creg_config()
        return self._make_config_probe('cfg_item_creg', config)

    def _make_cfg_value_creg_config(self):
        config = super()._make_cfg_value_creg_config()
        return self._make_config_probe('cfg_value_creg', config)

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
            config = ctl.merge(config, fixture_cfg)
        return self._make_config_probe(service_name, config)

    def bind_services(self, fn, params, requester=None):
        if inspect.ismethod(fn):
            probe = fn.__func__
            if isinstance(probe, ProbeBase):
                obj = fn.__self__
                fn = probe.real_fn.__get__(obj)
        return super().bind_services(fn, params, requester)

    def add_constructor(self, ctr):
        ctr_collector = self.resolve_service('ctr_collector')
        ctr_collector.add_constructor(ctr)

    def migrate_globals(self):
        for obj in list(self._globals):
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

    @property
    def used_keys(self):
        return self._used_keys
