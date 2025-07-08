from pathlib import Path

from . import htypes
from .services import (
    mosaic,
    )
from .code.config_layer import MutableConfigLayer



class FileBundleConfigLayer(MutableConfigLayer):

    def __init__(self, system, config_ctl, file_bundle_factory, path):
        super().__init__(system, config_ctl)
        self._bundle = file_bundle_factory(path, encoding=self._guess_encoding(path))

    @staticmethod
    def _guess_encoding(path):
        if path.suffix == '.json':
            return 'json'
        elif path.suffix == '.cdr':
            return 'cdr'
        else:
            raise RuntimeError(f"Unknown file bundle encoding suffix: {path.suffix!r}")

    def _load(self):
        try:
            piece = self._bundle.load_piece()
        except FileNotFoundError:
            return {}
        return self._data_to_config(piece)

    def _save(self):
        service_to_piece = {}
        for service_name, config in self.config.items():
            if not config:
                continue  # Do not add empty configs.
            ctl = self._config_ctl[service_name]
            piece = ctl.to_data(config)
            service_to_piece[service_name] = piece
        config_piece = htypes.system.system_config(
            services=tuple(
                htypes.system.service_config(
                    service=service_name,
                    config=mosaic.put(piece),
                    )
                for service_name, piece in service_to_piece.items()
                ),
            )
        self._bundle.save_piece(config_piece)


def load_config_layers(system, file_bundle_config_layer_factory, boot_config):
    for name, path in boot_config.config_layers.items():
        layer = file_bundle_config_layer_factory(Path.home() / path)
        system.load_config_layer(name, layer)
