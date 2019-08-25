#!/usr/bin/env python3

import sys
import logging
import argparse

from hyperapp.common.init_logging import init_logging
from hyperapp.client.application import Application


def main():
    init_logging('client')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    app = Application(sys.argv)
    app.run_event_loop()


main()
