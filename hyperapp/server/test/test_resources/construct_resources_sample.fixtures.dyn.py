import logging

from .htypes import construct_resources_sample

log = logging.getLogger(__name__)


def sample_servant_piece():
    log.info("Fixture sample_servant_piece is called")
    return construct_resources_sample.sample(id=123)


log.info("construct_resources_sample fixture module is loaded; sample_item: %s", construct_resources_sample.sample_item)
