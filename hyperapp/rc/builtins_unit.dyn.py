from .services import (
    builtin_services,
    )
from .code.dep import ServiceDep


class BuiltinsUnit:

    def __init__(self, ctx):
        self._ctx = ctx

    def init(self, graph):
        graph.name_to_unit['builtins'] = self
        for service_name in builtin_services:
            graph.dep_to_provider[ServiceDep(service_name)] = self

    def __repr__(self):
        return "<BuiltinsUnit>"

    @property
    def code_name(self):
        return None

    @property
    def is_fixtures(self):
        return False

    @property
    def is_tests(self):
        return False

    def provided_dep_resource(self, dep):
        return self._ctx.resource_registry['builtins', dep.resource_name]

    def is_up_to_date(self, graph):
        return True

    def new_test_imports_discovered(self, graph):
        pass
