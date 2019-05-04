import logging

from hyperapp.common.logger import RecordKind, LogRecord
from hyperapp.common.logger_json_storage import _RecordsToLineConverter

_log = logging.getLogger(__name__)


def test_record_to_line_converter():
    storage = _RecordsToLineConverter()
    record = LogRecord(RecordKind.ENTER, [1, 2], 'context_enter', dict(num=123, name='sam'))
    for line in storage.record2lines(record):
        _log.info("storage line: %r", line)
