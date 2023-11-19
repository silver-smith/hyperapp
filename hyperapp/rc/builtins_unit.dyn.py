from .services import (
    builtin_services,
    )
from .code.dep import ServiceDep


class BuiltinsUnit:

    def __init__(self, graph, ctx):
        self._graph = graph
        self._ctx = ctx

    def init(self):
        self._graph.name_to_unit['builtins'] = self
        for service_name in builtin_services:
            self._graph.dep_to_provider[ServiceDep(service_name)] = self

    def __repr__(self):
        return "<BuiltinsUnit>"

    @property
    def code_name(self):
        return None

    @property
    def is_builtins(self):
        return True

    @property
    def is_fixtures(self):
        return False

    @property
    def is_tests(self):
        return False

    def provided_dep_resource(self, dep):
        return self._ctx.resource_registry['builtins', dep.resource_name]

    @property
    def is_up_to_date(self):
        return True

    def new_test_imports_discovered(self):
        pass

    def new_service_provider_discovered(self, service_name, provider):
        pass

    async def run(self, process_pool):
        pass
