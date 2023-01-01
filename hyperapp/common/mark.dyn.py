
class Marker:

    def __init__(self, name):
        self._name = name

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        return Marker(f'{self._name}.{name}')

    def __call__(self, fn):
        return fn


param = Marker('param')
service = Marker('service')
