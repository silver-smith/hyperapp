import asyncio
import inspect
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


class UnknownServiceError(Exception):

    def __init__(self, service_name):
        super().__init__(f"Unknown service: {service_name!r}")
        self.service_name = service_name


@dataclass
class ServiceTemplateRec:

    module_name: str
    attr_name: str
    free_params: list[str]
    service_params: list[str]
    want_config: bool


class ServiceProbeTemplate:

    def __init__(self, module_name, attr_name, fn, params):
        self.module_name = module_name
        self.attr_name = attr_name
        self.fn = fn
        self.params = params

    def __repr__(self):
        return f"<ServiceProbeTemplate {self.module_name}:{self.attr_name} {self.fn} {self.params}>"

    def resolve(self, system, service_name):
        return ServiceProbe(system, self.module_name, self.attr_name, service_name, self.fn, self.params)


class FixtureProbeTemplate:

    def __init__(self, fn, params):
        self.fn = fn
        self.params = params

    def __repr__(self):
        return f"<FixtureProbeTemplate {self.fn} {self.params}>"

    def resolve(self, system, service_name):
        return FixtureProbe(system, service_name, self.fn, self.params)


class ConfigItemFixture:

    def __init__(self, fn, service_params):
        self._fn = fn
        self._service_params = service_params

    def __repr__(self):
        return f"<ConfigItemFixture {self._fn} {self._service_params}>"

    def resolve(self, system):
        service_args = [
            system.resolve_service(name)
            for name in self._service_params
            ]
        config = self._fn(*service_args)
        if not isinstance(config, dict):
            raise RuntimeError(f"Config item fixture should return a key->value dict ({self._fn}): {config!r}")
        return config


class Probe:

    def __init__(self, system_probe, service_name, fn, params):
        self._system = system_probe
        self._name = service_name
        self._fn = fn
        self._params = params
        self._resolved = False
        self._service = None

    def __call__(self, *args, **kw):
        free_param_count = len(args) + len(kw)
        service_params = self._params[:-free_param_count]
        return self._apply(service_params, *args, **kw)

    def __getattr__(self, name):
        service = self._apply(self._params)
        return getattr(service, name)

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
        self._service = service
        self._add_resolved_template(want_config, service_params)
        self._resolved = True
        return service

    def _run(self):
        return self._apply(self._params)

    def _add_resolved_template(self, want_config, template):
        pass


class ServiceProbe(Probe):

    def __init__(self, system_probe, module_name, attr_name, service_name, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._module_name = module_name
        self._attr_name = attr_name

    def __repr__(self):
        return f"<ServiceProbe {self._module_name}:{self._attr_name} {self._fn} {self._params}>"

    def _add_resolved_template(self, want_config, service_params):
        template = ServiceTemplateRec(
            module_name=self._module_name,
            attr_name=self._attr_name,
            free_params=self._params[len(service_params):],
            service_params=service_params,
            want_config=want_config,
            )
        self._system.add_resolved_template(self._name, template)


class FixtureProbe(Probe):

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params}>"


class SystemProbe:

    def __init__(self, configs, config_item_fixtures):
        self._configs = configs  # service_name -> key -> value
        self._config_item_fixtures = config_item_fixtures  # service_name -> fixture list
        self._name_to_template = configs['system']
        self._name_to_service = {}
        self._resolved_templates = {}

    def run(self, root_name):
        service = self.resolve_service(root_name)
        value = service._run()
        if inspect.iscoroutine(value):
            log.info("Running coroutine: %r", value)
            asyncio.run(value)

    @property
    def resolved_templates(self):
        return self._resolved_templates

    def resolve_config(self, service_name):
        config = {**self._configs.get(service_name, {})}
        for fixture in self._config_item_fixtures.get(service_name, []):
            cfg = fixture.resolve(self)
            config.update(cfg)
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

    def add_resolved_template(self, name, service):
        self._resolved_templates[name] = service

    def _raise_missing_service(self, service_name):
        raise UnknownServiceError(service_name)
