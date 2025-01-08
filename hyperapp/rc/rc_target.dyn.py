class TargetMissingError(Exception):
    pass


class Target:

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    @property
    def ready(self):
        return False

    @property
    def deps(self):
        return set()

    def update_status(self):
        pass

    @property
    def import_requirements(self):
        return set()

    @property
    def has_output(self):
        return False
