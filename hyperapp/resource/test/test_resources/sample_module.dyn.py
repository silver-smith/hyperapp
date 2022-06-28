import logging

log = logging.getLogger(__name__)


def test_one():
    pass


def test_two():
    pass


class SampleServant:

    def __init__(self, mosaic, web, peer_registry, rpc_call_factory):
        pass

    @property
    def _dict(self):
        return None

    def list(self, request):
        pass

    def list_live(self, request, peer_ref, servant_path_data):
        pass

    def open(self, request, current_key):
        pass


def sample_servant(mosaic, web, peer_registry, rpc_call_factory):
    log.info("Sample module: sample_factory call: %s, %s, %s, %s", mosaic, web, peer_registry, rpc_call_factory)
    return SampleServant(mosaic, web, peer_registry, rpc_call_factory)


log.info("Sample module module is loaded")
