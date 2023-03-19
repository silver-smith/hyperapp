from .services import (
    mark,
    )


class PhonyTransport:

    def send(self, receiver, sender_identity, ref_list):
        pass


@mark.service
def transport():
    return PhonyTransport()
