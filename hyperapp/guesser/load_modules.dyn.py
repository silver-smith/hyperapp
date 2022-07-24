from pathlib import Path

from .services import (
    code_module_loader,
    local_modules,
    local_types,
    type_module_loader,
    )


def load_additional_modules(dir_list):
    path_dir_list = [Path(d) for d in dir_list]
    type_module_loader.load_type_modules(path_dir_list, local_types)
    code_module_loader.load_code_modules(local_types, path_dir_list, local_modules)
