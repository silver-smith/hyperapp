import logging

from . import htypes

log = logging.getLogger(__name__)


class SampleList:

    def __init__(self, piece):
        log.info("sapmle/list: SampleList ctr: %s", piece.provider)

    def get(self):
        return [
            htypes.sample_list.item(1, 'First', 'First item'),
            htypes.sample_list.item(2, 'Second', 'Second item'),
            htypes.sample_list.item(3, 'Thirt', 'Third item'),
            ]

    def open(self, current_key):
        return f"Opened item: {current_key}"


def open_sample_list():
    return htypes.sample_list.sample_list(provider='client')


log.info("sample/list module is loaded")
