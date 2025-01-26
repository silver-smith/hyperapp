from .services import (
    web,
    )


# class SimpleConfigLayer:

#     def __init__(self, config):
#         self._config = config

#     @property
#     def config(self):
#         return self._config


class ConfigLayer:

    def __init__(self, system, config_ctl):
        self._system = system
        self._config_ctl = config_ctl

    def _data_to_config(self, config_piece):
        service_to_config_piece = {
            rec.service: web.summon(rec.config)
            for rec in config_piece.services
            }
        ordered_services = sorted(service_to_config_piece, key=self._system.service_config_order)
        service_to_config = {}
        for service_name in ordered_services:
            piece = service_to_config_piece.get(service_name)
            if not piece:
                continue
            ctl = self._config_ctl[service_name]
            config = ctl.from_data(piece)
            if service_name in {'config_ctl_creg', 'cfg_item_creg'}:
                # Subsequent ctl.from_data calls may already use it.
                self._system.update_service_config(service_name, config)
            if service_name == 'system':
                # Subsequent ctl.from_data calls may already use it.
                self._system.update_config_ctl(config)
            service_to_config[service_name] = config
        return service_to_config


class StaticConfigLayer(ConfigLayer):

    def __init__(self, system, config_ctl, config_piece):
        super().__init__(system, config_ctl)
        self._config_piece = config_piece

    @property
    def config(self):
        return self._data_to_config(self._config_piece)


class ProjectConfigLayer(ConfigLayer):

    def __init__(self, system, config_ctl, project):
        super().__init__(system, config_ctl)
        self._project = project

    @property
    def config(self):
        config_module_name = f'{self._project.name}.config'
        config_piece = self._project[config_module_name, 'config']
        return self._data_to_config(config_piece)
