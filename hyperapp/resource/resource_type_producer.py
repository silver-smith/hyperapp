
def resource_type_producer(resource_type_factory, resource_type_reg, resource_t):
    try:
        return resource_type_reg[resource_t]
    except KeyError:
        return resource_type_factory(resource_t)
