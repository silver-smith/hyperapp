import logging

from .htypes import sample_fixture

log = logging.getLogger(__name__)


log.info("sample_fixture is loaded")
log.info("sample_servant_d: %r", sample_fixture.sample_servant_d)
log.info("sample_item: %r", sample_fixture.sample_item)

sample_item = sample_fixture.sample_item(
    key=123,
    name="Some value",
    description="Some description",
    )
log.info("sample_item value: %r", sample_item)
