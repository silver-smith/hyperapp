import logging
import yaml
from functools import partial
from pathlib import Path

import pytest

from hyperapp.boot.htypes import Type, TList, TRecord, record_mt, list_mt
from hyperapp.boot.htypes.attribute import attribute_t
from hyperapp.boot.htypes.partial import partial_param_t, partial_t
from hyperapp.boot.htypes.builtin_service import builtin_service_t
from hyperapp.boot.association_registry import Association
from hyperapp.boot import cdr_coders  # self-registering

log = logging.getLogger(__name__)


pytest_plugins = [
    'hyperapp.boot.test.services',
    'hyperapp.boot.resource.test.services',
    ]

TEST_DIR = Path(__file__).parent.resolve()
TEST_RESOURCES_DIR = Path(__file__).parent / 'test_resources'


@pytest.fixture
def test_resources_dir():
    return TEST_RESOURCES_DIR


@pytest.fixture
def compare():
    def inner(resource_module, expected_fname):
        expected_yaml = TEST_DIR.joinpath(expected_fname + '.expected.yaml').read_text()
        actual_yaml = yaml.dump(resource_module.as_dict, sort_keys=False)
        Path(f'/tmp/{expected_fname}.resources.yaml').write_text(actual_yaml)
        assert actual_yaml == expected_yaml
    return inner


def test_load(resource_registry):
    servant_list = resource_registry['test-project.test_resources', 'servant_list']
    log.info("Servant list: %r", servant_list)

    sample_servant = resource_registry['test-project.test_resources', 'sample_servant']
    log.info("Sample servant: %r", sample_servant)


def test_set_attr(mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['test-project.sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_servant_2'] = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    assert res_module['sample_servant_2'] == attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    compare(res_module, 'test_set_attr')


def test_set_partial(htypes, mosaic, resource_registry, resource_module_factory, compare):
    sample_module_2 = resource_registry['test-project.sample_module_2', 'sample_module_2.module']
    res_module = resource_module_factory(resource_registry, 'test_module')
    attr = attribute_t(
        object=mosaic.put(sample_module_2),
        attr_name='sample_servant_2',
        )
    partial = partial_t(
        function=mosaic.put(attr),
        params=tuple([
            partial_param_t('mosaic', mosaic.put(builtin_service_t('mosaic'))),
            partial_param_t('web', mosaic.put(builtin_service_t('web'))),
            ]),
        )
    res_module['sample_servant_2'] = attr
    res_module['sample_servant_2_partial'] = partial
    assert res_module['sample_servant_2_partial'] == partial
    compare(res_module, 'test_set_partial')


def test_primitive(resource_registry, resource_module_factory, compare):
    res_module = resource_module_factory(resource_registry, 'test_module')
    res_module['sample_string'] = 'abcd efgh'
    res_module['sample_int'] = 12345
    compare(res_module, 'test_primitive')
    assert res_module['sample_int'] == 12345
    assert res_module['sample_string'] == 'abcd efgh'


# Extract from dynamic module base.type_reconstructor.
def list_type_to_piece(pyobj_creg, t):
    if isinstance(t, TList):
        return list_mt(
            element=pyobj_creg.actor_to_ref(t.element_t),
            )


def test_int_list(pyobj_creg, reconstructors, resource_registry, resource_module_factory, compare):
    reconstructors.append(partial(list_type_to_piece, pyobj_creg))
    res_module = resource_module_factory(resource_registry, 'test_module')
    value = (111, 222, 333)
    res_module['sample_list'] = value
    assert res_module['sample_list'] == value
    assert res_module.as_dict['definitions']['builtin-int-list']['value']['element'] == 'legacy_type.builtin:int'


def test_int_rec_list(pyobj_creg, reconstructors, htypes, resource_registry, resource_module_factory, compare):
    reconstructors.append(partial(list_type_to_piece, pyobj_creg))
    res_module = resource_module_factory(resource_registry, 'test_module')
    value = tuple(
        htypes.test_resources.int_rec(id)
        for id in [111, 222, 333]
        )
    res_module['sample_list'] = value
    assert res_module['sample_list'] == value
    assert (res_module.as_dict['definitions']['test_resources-int_rec-list']['value']['element']
            == 'legacy_type.test_resources:int_rec')


def test_ref_rec_list(mosaic, pyobj_creg, reconstructors, htypes, resource_registry, resource_module_factory, compare):
    reconstructors.append(partial(list_type_to_piece, pyobj_creg))
    res_module = resource_module_factory(resource_registry, 'test_module')
    value = tuple(
        htypes.test_resources.ref_rec(mosaic.put(id))
        for id in [111, 222, 333]
        )
    for id in [111, 222, 333]:
        res_module[f'int-{id}'] = id
    res_module['sample_list'] = value
    assert res_module['sample_list'] == value
    assert (res_module.as_dict['definitions']['test_resources-ref_rec-list']['value']['element']
            == 'legacy_type.test_resources:ref_rec')


def test_resolve_legacy_type(htypes, resource_registry, resource_module_factory, compare):
    res_module = resource_module_factory(resource_registry, 'test_module')
    test_d = htypes.test_resources.test_d
    res_module['test_d'] = test_d()
    compare(res_module, 'test_resolve_type')


# Partial copy of resource/type_reconstructor.dyn.py
def _type_to_piece(t):
    if not isinstance(t, Type):
        return None
    if isinstance(t, TRecord) and not t.fields and not t.base:
        return record_mt(
            module_name=t.module_name,
            name=t.name,
            base=None,
            fields=(),
            )
    raise RuntimeError(f"Test reconstructor: Unknown type: {t!r}")


def test_add_custom_type(htypes, resource_registry, resource_module_factory, reconstructors, compare):
    reconstructors.append(_type_to_piece)
    res_module = resource_module_factory(resource_registry, 'test_module')
    custom_d = TRecord('custom_module', 'custom_d_t')
    res_module['custom_d'] = custom_d()
    compare(res_module, 'test_add_custom_type')


def test_add_custom_type_matching_var_name(htypes, resource_registry, resource_module_factory, reconstructors, compare):
    reconstructors.append(_type_to_piece)
    res_module = resource_module_factory(resource_registry, 'test_module')
    custom_d = TRecord('custom_module', 'custom_d')
    with pytest.raises(RuntimeError) as excinfo:
        res_module['custom_d'] = custom_d()
    assert str(excinfo.value) == "Custom type name matches variable name: 'custom_d'"
