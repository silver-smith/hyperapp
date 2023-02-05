import logging

from . import htypes
from .services import (
    mark,
    mosaic,
    web,
    peer_registry,
    rpc_call_factory,
    )

log = logging.getLogger(__name__)


class SampleList:

    def __init__(self, piece):
        log.info("constuct_resources_sample: SampleServant ctr: %s", piece)

    def get(self):
        return [
            htypes.construct_resources_sample.sample_item(1, 'First', 'First item'),
            htypes.construct_resources_sample.sample_item(2, 'Second', 'Second item'),
            htypes.construct_resources_sample.sample_item(3, 'Thirt', 'Third item'),
            ]

    def open(self, current_key):
        pass

    def parent(self):
        pass


@mark.global_command
def sample_global_command():
    return htypes.construct_resources_sample.sample(123)


@mark.object_command
def sample_object_command(piece, view_state):
    pass


log.info("construct_resources_sample module is loaded, mosaic=%s, web=%s, peer_registry=%s, rpc_call_factory=%s",
         mosaic, web, peer_registry, rpc_call_factory)
