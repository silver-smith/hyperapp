import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class ServiceTemplate:

    module_name: str
    attr_name: str
    fn: callable
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
        return self._apply(self._params)

    def _apply(self, service_params, *args, **kw):
        if self._resolved:
            return self._service
        service_args = [
            self._system.resolve_service(name)
            for name in service_params
            ]
        service = self._fn(*service_args, *args, **kw)
        self._service = service
        self._add_resolved_template(service_params)
        self._resolved = True
        return service

    def _run(self):
        self._apply(self._params)

    def _add_resolved_template(self, template):
        pass


class ServiceProbe(Probe):

    def __init__(self, system_probe, module_name, attr_name, service_name, fn, params):
        super().__init__(system_probe, service_name, fn, params)
        self._module_name = module_name
        self._attr_name = attr_name

    def __repr__(self):
        return f"<ServiceProbe {self._module_name}:{self._attr_name} {self._fn} {self._params}>"

    def _add_resolved_template(self, service_params):
        template = ServiceTemplate(
            module_name=self._module_name,
            attr_name=self._attr_name,
            fn=self._fn,
            free_params=self._params[len(service_params):],
            service_params=service_params,
            want_config=False,
            )
        self._system.add_resolved_template(self._name, template)


class FixtureProbe(Probe):

    def __repr__(self):
        return f"<FixtureProbe {self._fn} {self._params}>"


class SystemProbe:

    def __init__(self, service_templates):
        self._name_to_template = service_templates
        self._name_to_service = {}
        self._resolved_templates = {}

    def run(self, root_name):
        service = self.resolve_service(root_name)
        service._run()

    @property
    def resolved_templates(self):
        return self._resolved_templates

    def resolve_service(self, name):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        template = self._name_to_template[name]
        service = template.resolve(self, name)
        self._name_to_service[name] = service
        return service

    def add_resolved_template(self, name, service):
        self._resolved_templates[name] = service
