import weakref


class SelfCommand:

    def __init__(self, object):
        self._piece = object.data
        self.kind = 'object'
        self.resource_key = None  # todo

    def is_enabled(self):
        return True

    async def run(self):
        return self._piece
