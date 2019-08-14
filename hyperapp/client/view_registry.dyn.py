import logging
from hyperapp.client.module import ClientModule

_log = logging.getLogger(__name__)


class NotApplicable(Exception):

    def __init__(self, object):
        super().__init__("This view producer is not applicable for object {}".format(object))


class ViewProducerRegistry:

    def __init__(self):
        self._producer_list = []

    def register_view_producer(self, producer):
        self._producer_list.append(producer)

    async def produce_view(self, piece, object, observer):
        for producer in self._producer_list:
            try:
                return (await producer(piece, object, observer))
            except NotApplicable:
                pass
        raise RuntimeError("No view is known to support object {}".format(object))


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        services.view_producer_registry = ViewProducerRegistry()
