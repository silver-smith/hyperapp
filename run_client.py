#!/usr/bin/env python3

import sys
import logging
import argparse

from hyperapp.common.init_logging import init_logging
from hyperapp.common.logger import log, logger_inited
from hyperapp.common.logger_json_storage import json_file_log_storage_session
from hyperapp.client.application import Application


def main():
    init_logging('client.yaml')
    with logger_inited(json_file_log_storage_session()):

        log.client_started()

        parser = argparse.ArgumentParser(description='Hyperapp client')
        args = parser.parse_args()

        app = Application(sys.argv)
        app.exec_()

        log.client_stopped()


main()
