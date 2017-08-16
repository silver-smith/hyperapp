
class Command(object):

    def __init__(self, id):
        assert isinstance(id, str), repr(id)
        self.id = id
