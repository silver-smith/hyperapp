from . import htypes
from .services import (
    mosaic,
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
            )


def load_build(root_dir):
    sources = [
        mosaic.put(src) for src
        in _load_pyhon_modules(root_dir)
        ]
    return htypes.build.full_build_task(sources)
