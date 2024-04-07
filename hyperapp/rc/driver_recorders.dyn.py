import logging
from collections import defaultdict
from contextlib import contextmanager

from . import htypes
from .services import (
    pyobj_creg,
    )

log = logging.getLogger(__name__)


class ImportRecorders:

    def __init__(self, import_recorders):
        self._recorder_dict = defaultdict(list)
        self.module_imports_list = None
        self._init(import_recorders)

    def _init(self, import_recorders):
        for rec in import_recorders:
            recorder = pyobj_creg.invite(rec.recorder)
            recorder.reset()
            self._recorder_dict[rec.module].append(recorder)

    def _save(self):
        module_to_imports = defaultdict(set)
        for module_name, recorder_list in self._recorder_dict.items():
            for recorder in recorder_list:
                module_to_imports[module_name] |= recorder.used_imports()
        log.info("Used imports: %s", module_to_imports)
        self.module_imports_list = tuple(
            htypes.inspect.module_imports(module_name, tuple(sorted(imports)))
            for module_name, imports in module_to_imports.items()
            )

    @contextmanager
    def recording(self):
        try:
            yield
        finally:
            self._save()
