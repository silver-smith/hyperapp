#!/usr/bin/env python3

import logging
import sys

from hyperapp.boot.init_logging import init_logging
from hyperapp.boot import cdr_coders  # register codec
from hyperapp.boot.services import HYPERAPP_DIR, Services

log = logging.getLogger('rc.main')


def main():
    init_logging('hyperapp')

    services = Services()
    services.init_services()
    log.debug("Initialized.")

    try:
        pyobj_creg = services.pyobj_creg
        project_factory = services.project_factory

        config_file = sys.argv[1]
        root_service = sys.argv[2]

        project = project_factory('everything')
        project.load(HYPERAPP_DIR)

        config = project[config_file, 'config']
        module_piece = project['base.system.system', 'system.module']
        module = pyobj_creg.animate(module_piece)

        module.run_system(config, root_service, project, sys.argv[3:])

    finally:
        log.info("Stopping.")
        services.stop()


if __name__ == '__main__':
    main()
