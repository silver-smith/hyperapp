from .tested.code import model_servant as model_servant_module


def test_model_servant(model_servant):
    model = "Sample model"
    servant = model_servant(model)
    assert isinstance(servant, model_servant_module.ModelServant)
