from pathlib import Path

from .services import (
    local_types,
    type_module_loader,
    )


def load_additional_modules(dir_list):
    path_dir_list = [Path(d) for d in dir_list]
    type_module_loader.load_type_modules(path_dir_list, local_types)
