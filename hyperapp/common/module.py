import logging

log = logging.getLogger(__name__)


MAX_INIT_PHASE_COUNT = 3


# base class for modules
class Module(object):

    def __init__(self, name, services, config):
        self.name = name

    def __repr__(self):
        return '<Module %r>' % self.name
