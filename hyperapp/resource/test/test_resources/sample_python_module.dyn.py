import logging

from . import htypes

log = logging.getLogger(__name__)


log.info("sample_python_module is loaded")
log.info("sample_servant_d: %r", htypes.sample_python_module.sample_servant_d)
log.info("sample_item: %r", htypes.sample_python_module.sample_item)

value = htypes.sample_python_module.sample_item(
    key=123,
    name="Some value",
    description="Some description",
    )
log.info("sample_item value: %r", value)
