

class Request(object):

    def __init__(self, command):
        self._command = command

    def make_response(self, result=None, error=None):
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
