import os.path
import glob
from ..common.util import is_list_list_inst
from ..common.htypes import tEndpoint
from ..common.identity import PublicKey
from ..common.endpoint import Endpoint
from ..common.packet_coders import packet_coders
from ..common.route_storage import RouteRepository


class FileRouteRepository(RouteRepository):

    fext = '.route.json'
    encoding = 'json_pretty'

    def __init__( self, dir ):
        self.dir = dir

    def enumerate( self ):
        for fpath in glob.glob(os.path.join(self.dir, '*' + self.fext)):
            yield self._load_item(fpath)

    def _load_item( self, fpath ):
        with open(fpath, 'rb') as f:
            data = f.read()
        rec = packet_coders.decode(self.encoding, data, tEndpoint)
        return Endpoint.from_data(rec)

    def add( self, public_key, routes ):
        assert isinstance(public_key, PublicKey), repr(public_key)
        assert is_list_list_inst(routes, str), repr(routes)
        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        endpoint = Endpoint(public_key, routes)
        data = packet_coders.encode(self.encoding, endpoint.to_data(), tEndpoint)
        fpath = os.path.join(self.dir, endpoint.public_key.get_id_hex() + self.fext)
        with open(fpath, 'wb') as f:
            f.write(data)
