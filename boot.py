#!/usr/bin/env python3

import logging
import sys

from hyperapp.boot.init_logging import init_logging
from hyperapp.boot import cdr_coders  # register codec
from hyperapp.boot.project import load_boot_config
from hyperapp.boot.services import HYPERAPP_DIR, Services

log = logging.getLogger('rc.main')


def main():
    init_logging('hyperapp')

    services = Services()
    services.init_services()
    log.debug("Initialized.")

    try:
        pyobj_creg = services.pyobj_creg
        load_projects = services.load_projects

        project_filter = sys.argv[1].split(',')
        root_service = sys.argv[2]

        boot_config = load_boot_config(HYPERAPP_DIR / 'projects.yaml')
        name_to_project = load_projects(boot_config, HYPERAPP_DIR, project_filter)

        system_module_piece = name_to_project['base']['base.system.system', 'system.module']
        system_module = pyobj_creg.animate(system_module_piece)

        system = system_module.System()
        system.load_projects(name_to_project.values())
        system['load_config_layers'](boot_config)
        system.set_default_layer(boot_config.default_layer)
        system['init_hook'].run_hooks()
        system.run(root_service, name_to_project, sys.argv[3:])

    finally:
        log.info("Stopping.")
        services.stop()


if __name__ == '__main__':
    main()
