#!/usr/bin/env python3

from datetime import datetime
import sys
import logging
import argparse
from pathlib import Path

from dateutil.tz import tzlocal

from hyperapp.common.init_logging import init_logging
from hyperapp.common.logger import log, logger_inited, json_file_log_storage
from hyperapp.client.application import Application


LOGS_DIR = Path('~/.local/share/hyperapp/client/logs').expanduser()


def main():
    init_logging('client.yaml')
    with logger_inited(json_file_log_storage(LOGS_DIR, datetime.now(tzlocal()))):
        with log.client_started():

            parser = argparse.ArgumentParser(description='Hyperapp client')
            args = parser.parse_args()

            app = Application(sys.argv)
            app.exec_()


main()
