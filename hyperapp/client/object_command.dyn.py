import inspect
import logging
import weakref

from hyperapp.client.commander import resource_key_of_class_method, UnboundCommand
from hyperapp.client.module import ClientModule

_log = logging.getLogger(__name__)


# decorator for object and module methods
class command:

    def __init__(self, id, kind=None):
        self.id = id
        self.kind = kind

    def __call__(self, class_method):
        resource_key = resource_key_of_class_method(class_method, 'command', self.id)
        return UnboundObjectCommand(self.id, self.kind, resource_key, class_method)


class UnboundObjectCommand(UnboundCommand):

    def __init__(self, id, kind, resource_key, class_method):
        self.id = id
        self.kind = kind
        self._resource_key = resource_key
        self._class_method = class_method

    def bind(self, object, kind):
        if self.kind is not None:
            kind = self.kind
        object_wr = weakref.ref(object)
        return BoundObjectCommand(self.id, kind, self._resource_key, self._class_method, object_wr)


class BoundObjectCommand:

    def __init__(self, id, kind, resource_key, class_method, object_wr, args=None, kw=None, wrapper=None, params_subst=None):
        self.id = id
        self.kind = kind
        self.resource_key = resource_key
        self._class_method = class_method
        self._object_wr = object_wr  # weak ref to object
        self._args = args or ()
        self._kw = kw or {}
        self._wrapper = wrapper
        self._params_subst = params_subst

    def __repr__(self):
        return (f"BoundObjectCommand(id={self.id} kind={self.kind} object={self._object_wr}"
                f" args={self._args} kw={self._kw} wrapper={self._wrapper})")

    def with_(self, **kw):
        old_kw = dict(
            id=self.id,
            kind=self.kind,
            resource_key=self.resource_key,
            class_method=self._class_method,
            object_wr=self._object_wr,
            args=self._args,
            kw=self._kw,
            wrapper=self._wrapper,
            params_subst=self._params_subst,
            )
        all_kw = {**old_kw, **kw}
        return BoundObjectCommand(**all_kw)

    def partial(self, *args, **kw):
        return self.with_(args=args, kw=kw)

    def is_enabled(self):
        return True  # todo

    async def run(self, *args, **kw):
        object = self._object_wr()
        if not object:
            return  # object we bound to is already deleted
        if self._params_subst:
            _log.info("BoundObjectCommand: subst params: (%r) args=%r kw=%r", self, args, kw)
            full_args, full_kw = self._params_subst(*self._args, *args, **self._kw, **kw)
        else:
            full_args = (*self._args, *args)
            full_kw = {**self._kw, **kw}
        if self._more_params_are_required(*full_args, **full_kw):
            signature = inspect.signature(self._class_method)
            bound_arguments = signature.bind_partial(object, *full_args, **full_kw)
            _log.info("BoundObjectCommand: run param editor: (%r) args=%r kw=%r", self, full_args, full_kw)
            result = await this_module.params_editor(object.data, self, bound_arguments, full_args, full_kw)
        else:
            result = await self._run_impl(object, full_args, full_kw)
        return (await self._wrap_result(result))

    async def run_with_full_params(self, *args, **kw):
        object = self._object_wr()
        if not object:
            return  # object we bound to is already deleted
        result = await self._run_impl(object, args, kw)
        return (await self._wrap_result(result))

    async def _run_impl(self, object, args, kw):
        _log.info("BoundObjectCommand: run: (%r) args=%r kw=%r", self, args, kw)
        if inspect.iscoroutinefunction(self._class_method):
            return (await self._class_method(object, *args, **kw))
        else:
            return self._class_method(object, *args, **kw)

    async def _wrap_result(self, result):
        if result is None:
            return
        piece = result
        object = await this_module.object_registry.resolve_async(piece)
        layout = await this_module.object_layout_producer.produce_layout(object)
        if self._wrapper:
            result = await self._wrapper(layout)
        return result

    def _more_params_are_required(self, *args, **kw):
        signature = inspect.signature(self._class_method)
        try:
            object = None
            signature.bind(object, *args, **kw)
            return False
        except TypeError as x:
            if str(x).startswith('missing a required argument: '):
                _log.info("More params are required: %s", x)
                return True
            else:
                raise


class ThisModule(ClientModule):

    def __init__(self, module_name, services):
        super().__init__(module_name, services)
        self.object_registry = services.object_registry
        self.object_layout_producer = services.object_layout_producer
        self.params_editor = services.params_editor
