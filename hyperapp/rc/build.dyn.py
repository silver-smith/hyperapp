from . import htypes
from .services import (
    local_types,
    mosaic,
    type_module_loader,
    )


def _load_pyhon_modules(root_dir):
    for path in root_dir.rglob('*.dyn.py'):
        rel_path = path.relative_to(root_dir)
        if 'test' in rel_path.parts:
            continue
        stem = path.name[:-len('.dyn.py')]
        dir = path.parent.relative_to(root_dir)
        dir_name = str(dir).replace('/', '.')
        name = f'{dir_name}.{stem}'
        yield htypes.build.python_module_src(
            name=name,
            path=str(rel_path),
            contents=path.read_text(),
            )


def _load_types(root_dir):
    types = local_types.copy()
    type_module_loader.load_type_modules([root_dir], types)
    for module_name, name_to_type in types.items():
        for name, type_piece in name_to_type.items():
            yield htypes.build.type_src(
                module_name=module_name,
                name=name,
                type=mosaic.put(type_piece),
                )


def load_build(root_dir):
    return htypes.build.full_build_task(
        types=tuple(_load_types(root_dir)),
        python_modules=tuple(_load_pyhon_modules(root_dir)),
        )

