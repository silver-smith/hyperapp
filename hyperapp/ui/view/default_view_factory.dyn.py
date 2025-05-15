from .code.mark import mark


@mark.service
def default_model_factory(config, view_factory_reg, model_t):
    k = config[model_t]
    return view_factory_reg[k]
