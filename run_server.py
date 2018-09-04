#!/usr/bin/env python3

import logging
import argparse
import time
from pathlib import Path

from types import SimpleNamespace
from hyperapp.common.init_logging import init_logging
from hyperapp.common.identity import Identity
from hyperapp.server.services import Services

log = logging.getLogger(__name__)


DEFAULT_ADDR = 'localhost:8888'


def main():
    init_logging('server.yaml')

    parser = argparse.ArgumentParser(description='Hyperapp server')
    parser.add_argument('identity_fpath', type=Path, help='path to identity file')
    parser.add_argument('addr', nargs='?', help='address to listen at', default=DEFAULT_ADDR)
    parser.add_argument('--test-delay', type=float, help='artificial delay for handling requests, seconds')
    args = parser.parse_args()

    identity = Identity.load_from_file(args.identity_fpath)
    start_args = SimpleNamespace(identity=identity, addr=args.addr, test_delay=args.test_delay)
    services = Services(start_args)
    services.start()
    try:
        while services.is_running:
            try:
                time.sleep(0.3)
            except KeyboardInterrupt:
                break
    finally:
        services.stop()


main()
