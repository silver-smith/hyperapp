import logging

log = logging.getLogger(__name__)


def _callback():
    log.info("Test rpc subprocess callback is called")
    return 'ok'
