from hyperapp.boot.htypes.packet_coders import packet_coders

from . import htypes
from .services import (
    web,
    )
from .code.mark import mark


def _reconstruct_bundle(piece):
    return htypes.builtin.bundle(
        roots=piece.roots,
        associations=piece.associations,
        capsule_list=tuple(
            web.pull(ref) for ref in piece.capsules
            ),
        )


@mark.model
def bundle_info(piece, format):
    bundle = _reconstruct_bundle(piece)
    bundle_cdr = packet_coders.encode('cdr', bundle, htypes.builtin.bundle)
    capsule_count = len(piece.capsules)
    capsule_len_list = [len(capsule.encoded_object) for capsule in bundle.capsule_list]
    capsule_data_size_sum = sum(capsule_len_list)
    return htypes.bundle_info.bundle_info(
        root_title=format(web.summon(piece.roots[0])),
        association_count=len(piece.associations),
        cdr_encoded_size=len(bundle_cdr),
        capsule_count=capsule_count,
        capsule_data_size_sum=capsule_data_size_sum,
        capsule_data_size_average=capsule_data_size_sum // capsule_count,
        capsule_data_size_min=min(capsule_len_list),
        capsule_data_size_max=max(capsule_len_list),
        )


@mark.command
def open_root(piece):
    return htypes.data_browser.record_view(
        data=piece.roots[0],
        )


@mark.command
def open_capsules(piece):
    return htypes.bundle_info.capsule_list_model(
        bundle_name=piece.bundle_name,
        capsules=piece.capsules,
        )


def _capsule_item_list(ref_list):
    item_list = []
    for ref in ref_list:
        capsule = web.pull(ref)
        item = htypes.bundle_info.capsule_item(
            ref=ref,
            data_size=len(capsule.encoded_object),
            type_ref=capsule.type_ref,
            type_str=format(web.summon(capsule.type_ref)),
            title=format(web.summon(ref)),
            )
        item_list.append(item)
    return item_list


@mark.model
def capsule_list(piece, format):
    return _capsule_item_list(piece.capsules)


@mark.command
def open_capsule(piece, current_item):
    return htypes.data_browser.record_view(
        data=current_item.ref,
        )


@mark.command
def open_associations(piece):
    return htypes.bundle_info.ass_list_model(
        bundle_name=piece.bundle_name,
        associations=piece.associations,
        )


@mark.model
def ass_list(piece, format):
    return _capsule_item_list(piece.associations)


@mark.command
def open_association(piece, current_item):
    return htypes.data_browser.record_view(
        data=current_item.ref,
        )


@mark.actor.formatter_creg
def format_model(piece):
    return f"Bundle: {piece.bundle_name}"


@mark.actor.formatter_creg
def format_capsule_list_model(piece):
    return f"Bundle capsules: {piece.bundle_name}"


@mark.actor.formatter_creg
def format_ass_list_model(piece):
    return f"Bundle associations: {piece.bundle_name}"
