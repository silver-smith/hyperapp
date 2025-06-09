from . import htypes
from .code.mark import mark
from .code.list_diff import KeyListDiff


def _item_count(config_template):
    if type(config_template) is dict:
        return len(config_template)
    else:
        return None


def _service_item(system, assoc_key, format, service_name):
    return htypes.config_service_list.item(
        service_name=service_name,
        item_count=_item_count(system.get_config_template(service_name)),
        assoc=format(assoc_key.get(service_name)),
        )


@mark.model(key='service_name')
def config_service_list(piece, format, assoc_key, system):
    return [
        _service_item(system, assoc_key, format, service_name)
        for service_name in sorted(system.service_names)
        ]


@mark.command
async def toggle_assoc(piece, current_key, feed_factory, format, assoc_key, system):
    service_name = current_key
    feed = feed_factory(piece)
    ass = htypes.assoc_key.key_base_association()
    if service_name in assoc_key:
        del assoc_key[service_name]
    else:
        assoc_key[service_name] = ass
    item = _service_item(system, assoc_key, format, service_name)
    await feed.send(KeyListDiff.Replace(service_name, item))


@mark.global_command
def open_config_service_list():
    return htypes.config_service_list.model()
