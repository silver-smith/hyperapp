
from ..common.interface import hyper_ref as href_types
from ..common.htypes import EncodableEmbedded


class Request(object):

    def __init__(self, command):
        self._command = command

    def make_response(self, result=None, error=None):
        assert self._command.is_request, 'This is not a request, response is not expected here'
        result_t = self._command.response
        if result is None and error is None:
            result = result_t()
        assert result is None or isinstance(result, result_t), \
          'result for %s is expected to be %r, but is %r' % (self._command.full_name, result_t, result)
        return Response(result, error)
    
    def make_response_result(self, *args, **kw):
        return self.make_response(result=self._command.response(*args, **kw))


class Response(object):

    def __init__(self, result, error):
        self._result = result
        self._error = error

    def make_rpc_response(self, command, request_id):
        if self._error:
            assert 0  # todo
        return href_types.rpc_response(
            request_id=request_id,
            is_succeeded=True,
            result_or_error=EncodableEmbedded(command.response, self._result),
            )
