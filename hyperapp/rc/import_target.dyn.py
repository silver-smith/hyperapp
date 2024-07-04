from .code.import_job import ImportJob


class ImportTarget:

    def __init__(self, python_module_src, type_src_list, idx=1):
        self._python_module_src = python_module_src
        self._type_src_list = type_src_list
        self._idx = idx
        self._key = ('import_target', self._python_module_src.name, self._idx)
        self._completed = False

    def __eq__(self, rhs):
        return type(rhs) is ImportTarget and self._key == rhs._key

    def __hash__(self):
        return hash(self._key)

    @property
    def name(self):
        return f'import/{self._python_module_src.name}/{self._idx}'

    @property
    def ready(self):
        return True

    @property
    def completed(self):
        return self._completed

    @property
    def job(self):
        return ImportJob(self._python_module_src, self._idx)

    def set_job_result(self, result):
        self._completed = True
