
# base class for modules
class Module(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Module %r>' % self.name
