class ServiceProbeTemplate:

    def __init__(self, fn, params):
        self.fn = fn
        self.params = params

    def __repr__(self):
        return f"<ServiceProbeTemplate {self._fn} {self.params}>"

    def resolve(self, system):
        return ServiceProbe(system, self.fn, self.params)


class ServiceProbe:

    def __init__(self, system_probe, fn, params):
        self._system = system_probe
        self._fn = fn
        self._params = params
        self._resolved = False
        self._service = None

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
            return self._service
        service_kw = {
            name: self._system._resolve_service(name)
            for name in service_params
            }
        service = self._fn(*args, **kw, **service_kw)
        self._service = service
        self._resolved = True
        return service

    def _run(self):
        self._apply(self._params)


class SystemProbe:

    def __init__(self, service_templates):
        self._name_to_template = service_templates
        self._name_to_service = {}

    def run(self, root_name):
        template = self._name_to_template[root_name]
        self._run(template)

    def _run(self, template):
        service = template.resolve(self)
        service._run()

    def _resolve_service(self, name):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        template = self._name_to_template[name]
        service = template.resolve(self)
        self._name_to_service[name] = service
        return service
