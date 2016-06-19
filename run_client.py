#!/usr/bin/env python3

import sys
import logging
import argparse
from hyperapp.client.application import Application


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s  %(message)s')

    parser = argparse.ArgumentParser(description='Hyperapp client')
    args = parser.parse_args()

    app = Application(sys.argv)
    app.exec_()


main()
