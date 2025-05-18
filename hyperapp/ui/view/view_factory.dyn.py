import inspect

from . import htypes
from .services import (
    mosaic,
    pyobj_creg,
    web,
    )
from .code.mark import mark
from .code.remote_model import real_model_t


class ViewFactoryBase:

    def __init__(self, model_t, ui_t_t):
        assert not (model_t is not None and ui_t_t is not None)  # Not both.
        self._model_t = model_t
        self._ui_t_t = ui_t_t

    def match_model(self, model_t, ui_t, only_model):
        if self._model_t is not None:
            return model_t is self._model_t
        if self._ui_t_t is not None:
            return isinstance(ui_t, self._ui_t_t)
        return not only_model


class ViewFactory(ViewFactoryBase):

    def __init__(self, format, visualizer_reg, k, model_t, ui_t_t, view_t, is_wrapper, view_ctx_params, system_fn):
        super().__init__(model_t, ui_t_t)
        self._format = format
        self._visualizer_reg = visualizer_reg
        self._k = k
        self._view_t = view_t
        self._is_wrapper = is_wrapper
        self._view_ctx_params = view_ctx_params
        self._system_fn = system_fn

    @property
    def k(self):
        return self._k

    async def call(self, ctx, accessor=None):
        if accessor is None:
            accessor = htypes.accessor.model_accessor()
        if self._ui_t_t is not None:
            model_t = real_model_t(ctx.model)
            ui_t, system_fn = self._visualizer_reg(model_t)
            return self.call_ui_t(ctx, ui_t, system_fn, accessor)
        fn_ctx = ctx.clone_with(
            model_t=self._model_t,
            )
        result = self._system_fn.call(fn_ctx, accessor=accessor)
        return await self._await_if_coro(result)

    async def call_ui_t(self, ctx, ui_t, system_fn, accessor=None):
        assert self._ui_t_t is not None
        if accessor is None:
            accessor = htypes.accessor.model_accessor()
        fn_ctx = ctx.clone_with(
            piece=ui_t,
            system_fn=system_fn,
            )
        result = self._system_fn.call(fn_ctx, accessor=accessor)
        return await self._await_if_coro(result)

    @staticmethod
    async def _await_if_coro(result):
        if inspect.iscoroutine(result):
            return await result
        else:
            return result

    @property
    def item(self):
        return htypes.view_factory.item(
            k=mosaic.put(self._k),
            title=self._format(self._k),
            view_t=pyobj_creg.actor_to_ref(self._view_t),
            view_t_str=str(self._view_t),
            is_wrapper=self._is_wrapper,
            view_ctx_params=tuple(self._view_ctx_params),
            model_t=None,
            )

    def get_item_list(self, ctx, model):
        return [self.item]


class ViewMultiFactoryItem:

    def __init__(self, k, get_fn):
        self._k = k
        self._get_fn = get_fn

    async def call(self, ctx, accessor=None):
        if accessor is None:
            accessor = htypes.accessor.model_accessor()
        return await self._get_fn.call(ctx, k=self._k, accessor=accessor)


class ViewMultiFactory(ViewFactoryBase):

    def __init__(self, format, visualizer_reg, k, model_t, ui_t_t, list_fn, get_fn):
        super().__init__(model_t, ui_t_t)
        self._format = format
        self._visualizer_reg = visualizer_reg
        self._k = k
        self._list_fn = list_fn
        self._get_fn = get_fn

    def get_item_list(self, ctx, model):
        if model is None:
            # model_factory_reg.items(model_t) variant is not supported by multi factory.
            return []
        model_ctx = ctx.clone_with(
            model=model,
            piece=model,
            )
        k_list = self._list_fn.call(model_ctx)
        item_list = []
        for k in k_list:
            multi_k = htypes.view_factory.multi_item_k(
                factory_k=mosaic.put(self._k),
                item_k=mosaic.put(k),
                )
            item = htypes.view_factory.item(
                k=mosaic.put(multi_k),
                title=self._format(k),
                view_t=None,
                view_t_str="",
                is_wrapper=False,
                view_ctx_params=(),
                model_t=None,
                )
            item_list.append(item)
        return item_list

    def get_item(self, k):
        return ViewMultiFactoryItem(k, self._get_fn)


class ViewFactoryReg:

    def __init__(self, visualizer_reg, config):
        self._visualizer_reg = visualizer_reg
        self._config = config

    def __getitem__(self, k):
        if not isinstance(k, htypes.view_factory.multi_item_k):
            return self._config[k]
        factory_k = web.summon(k.factory_k)
        item_k = web.summon(k.item_k)
        factory = self._config[factory_k]
        return factory.get_item(item_k)

    def items(self, ctx, model=None, model_t=None, only_model=False):
        if model is None and model_t is None:
            ui_t = None
        else:
            if model_t is None:
                model_t = real_model_t(model)
            try:
                ui_t, unused_system_fn = self._visualizer_reg(model_t)
            except KeyError:
                ui_t = None
        item_list = []
        for factory in self._config.values():
            if factory.match_model(model_t, ui_t, only_model):
                item_list += factory.get_item_list(ctx, model)
        return item_list


# d -> ViewFactory.
@mark.service
def view_factory_reg(config, visualizer_reg):
    return ViewFactoryReg(visualizer_reg, config)
