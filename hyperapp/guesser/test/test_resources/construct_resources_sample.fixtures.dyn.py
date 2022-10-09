import logging

from . import htypes
from .marker import param

log = logging.getLogger(__name__)


param.SampleServant.piece = htypes.construct_resources_sample.sample(id=123)
param.sample_command.adapter = None


log.info("construct_resources_sample fixture module is loaded; sample_item: %s", htypes.construct_resources_sample.sample_item)
