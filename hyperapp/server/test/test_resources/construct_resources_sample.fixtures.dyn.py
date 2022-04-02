import logging

from .htypes import construct_resources_sample

log = logging.getLogger(__name__)


def sample_servant_piece():
    return 'test value'


log.info("construct_resources_sample fixture module is loaded; sample_item: %s", construct_resources_sample.sample_item)
