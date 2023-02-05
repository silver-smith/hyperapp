import logging

from . import htypes
from .services import mark

log = logging.getLogger(__name__)


@mark.param.SampleList
def piece():
    return htypes.construct_resources_sample.sample(id=123)


@mark.param.SampleList.open
def current_key():
    return None


@mark.param.sample_object_command
def piece():
    return None


@mark.param.sample_object_command
def view_state():
    return None


log.info("construct_resources_sample fixture module is loaded; sample_item: %s", htypes.construct_resources_sample.sample_item)
