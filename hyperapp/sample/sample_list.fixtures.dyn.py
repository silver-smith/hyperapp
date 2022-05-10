import logging

from .htypes import sample_list

log = logging.getLogger(__name__)


def sample_list_piece():
    log.info("Fixture sample_list_piece is called")
    return sample_list.sample_list()


log.info("sample/list fixture module is loaded; piece t: %s", sample_list.sample_list)
