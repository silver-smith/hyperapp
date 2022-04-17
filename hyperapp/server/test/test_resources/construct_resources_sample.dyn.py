import logging

from . import htypes

log = logging.getLogger(__name__)


class SampleServant:

    def __init__(self, piece, mosaic, web, peer_registry, rpc_call_factory):
        log.info("constuct_resources_sample: SampleServant ctr: %s, %s, %s, %s", mosaic, web, peer_registry, rpc_call_factory)

    @property
    def _dict(self):
        return None

    def list(self, request):
        return [
            htypes.construct_resources_sample.sample_item(1, 'First', 'First item'),
            htypes.construct_resources_sample.sample_item(2, 'Second', 'Second item'),
            htypes.construct_resources_sample.sample_item(3, 'Thirt', 'Third item'),
            ]

    def list_live(self, request, peer_ref, servant_path_data):
        pass

    def open(self, request, current_key):
        pass

    def parent(self, request):
        pass


log.info("construct_resources_sample module is loaded")
