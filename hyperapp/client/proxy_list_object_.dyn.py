import asyncio
from .module import Module


class ProxyListObject(object):

    def __init__(self, url):
        self._proxy = this_module.proxy_factory.from_url(url)
        self._subscribed = None  # todo

    @asyncio.coroutine
    def fetch_elements(self, sort_column_id, from_key, desc_count, asc_count):
        log.info('-- ProxyListObject fetch_elements self=%r subscribed=%r from_key=%r desc_count=%r asc_count=%r',
                 id(self), self._subscribed, from_key, desc_count, asc_count)
        pass


class ThisModule(Module):

    def __init__(self, services):
        Module.__init__(self, services)
        self.proxy_factory = services.proxy_factory
