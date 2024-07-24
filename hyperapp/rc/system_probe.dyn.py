import logging

log = logging.getLogger(__name__)


class Service:

    def __init__(self, fn, free_params, service_params, want_config):
        self._fn = fn
        self._free_params = free_params
        self._service_params = service_params
        self._want_config = want_config

    def __repr__(self):
        return f"<Service {self._fn} {self._free_params}/{self._service_params}/{self._want_config}>"


class ServiceProbeTemplate:

    def __init__(self, fn, params):
        self.fn = fn
        self.params = params

    def __repr__(self):
        return f"<ServiceProbeTemplate {self._fn} {self.params}>"

    def resolve(self, system, service_name):
        return ServiceProbe(system, service_name, self.fn, self.params)


class ServiceProbe:

    def __init__(self, system_probe, service_name, fn, params):
        self._system = system_probe
        self._name = service_name
        self._fn = fn
        self._params = params
        self._resolved = False
        self._service_obj = None

    def __repr__(self):
        return f"<ServiceProbe {self._fn} {self._params}>"

    def __call__(self, *args, **kw):
        free_params = {*self._params[:len(args)], *kw}
        service_params = set(self._params) - free_params
        return self._apply(service_params, *args, **kw)

    def __getattr__(self, name):
        return self._apply(self._params)

    def _apply(self, service_params, *args, **kw):
        if self._resolved:
            return self._service_obj
        service_kw = {
            name: self._system.resolve_service(name)
            for name in service_params
            }
        service_obj = self._fn(*args, **kw, **service_kw)
        self._service_obj = service_obj
        service = Service(
            fn=self._fn,
            free_params=[*self._params[:len(args)], *kw],
            service_params=list(service_kw),
            want_config=False,
            )
        self._system.add_resolved_service(self._name, service)
        self._resolved = True
        return service_obj

    def _run(self):
        self._apply(self._params)


class SystemProbe:

    def __init__(self, service_templates):
        self._name_to_template = service_templates
        self._name_to_service = {}
        self._resolved_services = {}

    def run(self, root_name):
        service = self.resolve_service(root_name)
        service._run()
        for name, service in self._resolved_services.items():
            log.info("Resolved service %s: %s", name, service)

    def resolve_service(self, name):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        template = self._name_to_template[name]
        service = template.resolve(self, name)
        self._name_to_service[name] = service
        return service

    def add_resolved_service(self, name, service):
        self._resolved_services[name] = service
