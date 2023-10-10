
class BuiltinsUnit:

    def __repr__(self):
        return "<BuiltinsUnit>"

    @property
    def is_fixtures(self):
        return False

    @property
    def is_tests(self):
        return False

    def is_up_to_date(self, graph):
        return True
