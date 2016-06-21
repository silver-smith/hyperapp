from .htypes import tUrl
from .visitor import Visitor


class ServerPksCollector(Visitor):

    def collect_public_key_ders( self, t, value ):
        self._collected_pks = set()
        self.visit(t, value)
        return list(self._collected_pks)

    def visit_record( self, t, value ):
        if t is tUrl:
            self._collected_pks.add(value.endpoint.public_key_der)
