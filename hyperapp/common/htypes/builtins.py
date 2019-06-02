from collections import OrderedDict

from .htypes import TString, tString, tBinary, TList
from .record import TRecord


tRoute = TList(tString, name='route')

tServerRoutes = TRecord('server_routes', OrderedDict([
    ('public_key_der', tBinary),
    ('routes', TList(tRoute)),
    ]))

tIfaceId = TString(name='iface_id')

tPath = TList(tString, name='path')

tUrl = TRecord('url', OrderedDict([
    ('iface', tIfaceId),
    ('public_key_der', tBinary),
    ('path', tPath),
    ]))

tUrlWithRoutes = TRecord('url_with_routes', base=tUrl, fields=OrderedDict([
    ('routes', TList(tRoute)),
    ]))
