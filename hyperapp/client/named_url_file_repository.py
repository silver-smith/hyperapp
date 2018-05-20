# store urls with associated name in file directory, one file for item, in json, using id as file name

import os.path
import abc
import glob
from ..common.htypes import (
    tString,
    Field,
    TRecord,
    tUrl,
#    IfaceRegistry,
    )
from ..common.url import Url
from ..common.packet_coders import packet_coders


class NamedUrl(object):

    type = TRecord([
        Field('name', tString),
        Field('url', tUrl),
        ])

    @classmethod
    def from_data(cls, iface_registry, id, rec):
        assert isinstance(rec, cls.type), repr(rec)
        return cls(id, rec.name, Url.from_data(iface_registry, rec.url))

    def __init__(self, id, name, url):
        assert isinstance(id, str), repr(id)
        assert isinstance(name, str), repr(name)
        assert isinstance(url, Url), repr(url)
        self.id = id
        self.name = name
        self.url = url

    def to_data(self):
        return self.type(self.name, self.url.to_data())


class NamedUrlRepository(object, metaclass=abc.ABCMeta):

    # returns Item list/iterator
    @abc.abstractmethod
    def enumerate(self):
        pass

    @abc.abstractmethod
    def add(self, item):
        pass


class FileNamedUrlRepository(NamedUrlRepository):

    fext = '.url.json'
    encoding = 'json'

    def __init__(self, iface_registry, dir):
        assert isinstance(iface_registry, IfaceRegistry), repr(iface_registry)
        self.iface_registry = iface_registry
        self.dir = dir

    def enumerate(self):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            yield self._load_item(fpath)

    def add(self, item):
        assert isinstance(item, NamedUrl), repr(item)
        self._save_item(item)

    def _load_item(self, fpath):
        fname = os.path.basename(fpath)
        name, ext = os.path.splitext(fname)  # file name is NamedUrl.id
        with open(fpath, 'rb') as f:
            data = f.read()
        rec = packet_coders.decode(self.encoding, data, NamedUrl.type)
        return NamedUrl.from_data(self.iface_registry, name, rec)

    def _save_item(self, item):
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        data = packet_coders.encode(self.encoding, item.to_data(), NamedUrl.type)
        fpath = os.path.join(self.dir, item.id + self.fext)
        with open(fpath, 'wb') as f:
            f.write(data)
