import logging

log = logging.getLogger(__name__)


def process_main(connection, received_refs, name):
    my_name = "Subprocess test main"
    log.info("%s: Started", my_name)
    try:
        value = connection.recv()
        log.info("%s: Received: %s", my_name, value)
    except EOFError as x:
        log.info("%s: Connection EOF: %s", my_name, x)
    except ConnectionResetError as x:
        log.info("%s: Connection reset: %s", my_name, x)
