class ServiceProbe:

    def __init__(self, fn, params):
        self._fn = fn
        self._params = params

    def __repr__(self):
        return f"<ServiceProbe {self._fn} {self._params}>"


class SystemProbe:

    def __init__(self, service_templates):
        self._name_to_template = service_templates

    def run(self, root_name):
        assert 0, (root_name, self._name_to_template)
