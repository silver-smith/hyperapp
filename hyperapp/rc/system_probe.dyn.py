class ServiceProbe:

    def __init__(self, fn, params):
        self._fn = fn
        self.params = params

    def __repr__(self):
        return f"<ServiceProbe {self._fn} {self.params}>"

    def run(self, params):
        return self._fn(*params)


class SystemProbe:

    def __init__(self, service_templates):
        self._name_to_template = service_templates
        self._name_to_service = {}

    def run(self, root_name):
        template = self._name_to_template[root_name]
        self._run(template)

    def _run(self, template):
        params = [self._resolve_service(name) for name in template.params]
        return template.run(params)

    def _resolve_service(self, name):
        try:
            return self._name_to_service[name]
        except KeyError:
            pass
        template = self._name_to_template[name]
        service = self._run(template)
        self._name_to_service[name] = service
        return service
