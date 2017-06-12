from ..htypes import make_request_types


def test_response_result_should_be_subclass_of_response():
    rt = make_request_types().to_namespace()
    assert issubclass(rt.result_response_rec, rt.response_rec)
    assert issubclass(rt.result_response, rt.response)
    
