import weakref


class SelfCommand:

    def __init__(self, id, object):
        self.id = id
        self.kind = 'object'
        self.resource_key = None  # todo
        self._piece = object.data

    def is_enabled(self):
        return True

    async def run(self):
        return self._piece
