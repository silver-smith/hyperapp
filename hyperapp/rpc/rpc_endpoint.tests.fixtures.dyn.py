from .services import (
    mark,
    )

class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()


class PhonyPythonObjectCReg:

    def __init__(self):
        self._phony_servant = None

    def set_phony_servant(self, fn):
        self._phony_servant = fn

    def invite(self, servant_ref):
        return self._phony_servant


@mark.service
def python_object_creg():
    return PhonyPythonObjectCReg()
