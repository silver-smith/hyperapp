from .services import (
    builtin_services,
    )
from .code.dep import ServiceDep


class BuiltinsUnit:

    def init(self, graph):
        graph.name_to_unit['builtins'] = self
        for service_name in builtin_services:
            graph.dep_to_provider[ServiceDep(service_name)] = self

    def __repr__(self):
        return "<BuiltinsUnit>"

    @property
    def is_fixtures(self):
        return False

    @property
    def is_tests(self):
        return False

    def is_up_to_date(self, graph):
        return True
