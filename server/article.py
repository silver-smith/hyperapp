import json
from pony.orm import db_session, commit, Required, Optional, Set, select
from util import str2id
from common.interface.article import article_iface, ref_list_iface, object_selector_iface, onwrap_object_selector_iface
from common.request import Diff, ListDiff, Command, Element, Column
from object import Object, ListObject, ListObjectElement, subscription
from module import ModuleCommand
from ponyorm_module import PonyOrmModule


MODULE_NAME = 'article'


class TextDiff(Diff):

    def __init__( self, text ):
        self.text = text

    def as_json( self ):
        return dict(
            text=self.text)


class Article(Object):

    mode_view = object()
    mode_edit = object()

    iface = article_iface
    proxy_id = 'text'

    class_registry = {}  # ponyorm entity class -> class

    @classmethod
    def register_class( cls, ponyorm_entity_class ):
        cls.class_registry[ponyorm_entity_class] = cls

    @classmethod
    def from_rec( cls, article_rec ):
        real_cls = cls.class_registry[article_rec.__class__]
        return real_cls(real_cls.make_path(article_rec.id), article_rec.id)

    @classmethod
    def make_path( cls, article_id ):
        return module.make_path(object='article', article_id=article_id)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id=article_id)

    @classmethod
    def make_new( cls ):
        article_id = None
        path = cls.make_path(article_id)
        return cls(path, article_id=article_id, mode=cls.mode_edit)

    def __init__( self, path, article_id, mode=mode_view ):
        assert mode in [self.mode_view, self.mode_edit], repr(mode)
        Object.__init__(self, path)
        self.article_id = article_id
        if mode == self.mode_view:
            self.view_id = 'text_view'
        else:
            self.view_id = 'text_edit'

    @db_session
    def get_contents( self, **kw ):
        if self.article_id is not None:
            rec = module.Article[self.article_id]
            text = rec.text
        else:
            text = None
        return Object.get_contents(self, text=text, **kw)

    def get_commands( self ):
        return [
            Command('edit', 'Edit', 'Switch to edit mode', 'E'),
            Command('view', 'View', 'Finish editing, switch to view mode', 'Ctrl+F'),
            Command('save', 'Save', 'Save article', 'Ctrl+S'),
            Command('refs', 'Refs', 'Open article references', 'Ctrl+R'),
            ]

    def process_request( self, request ):
        # view and edit commands are expected to be handled by client side enterely
        if request.command_id == 'save':
            return self.run_command_save(request)
        elif request.command_id == 'refs':
            return self.run_command_refs(request)
        elif request.command_id == 'open_ref':
            return self.run_command_open_ref(request)
        else:
            return Object.process_request(self, request)

    def run_command_save( self, request ):
        return self.do_save(request, request.params.text)

    def run_command_refs( self, request ):
        return request.make_response_object(ArticleRefList.make(self.article_id))

    @db_session
    def run_command_open_ref( self, request ):
        ref_id = request.params.ref_id
        rec = module.ArticleRef[ref_id]
        target_path = json.loads(rec.path)
        target = module.run_resolve(target_path)
        return request.make_response_object(target)

    @db_session
    def do_save( self, request, text ):
        if self.article_id is not None:
            article_rec = module.Article[self.article_id]
            article_rec.text = text
        else:
            article_rec = module.Article(text=text)
        commit()
        print 'Article is saved, article_id =', article_rec.id
        diff = TextDiff(text)
        new_path = dict(self.path, article_id=article_rec.id)
        subscription.distribute_update(new_path, diff)
        return request.make_response_result(new_path=new_path)


class ArticleRefList(ListObject):

    iface = ref_list_iface
    proxy_id = 'ref_list'
    view_id = 'list'

    columns = [
        Column('key', 'Ref id'),
        Column('path', 'Path'),
        ]

    def __init__( self, path, article_id ):
        ListObject.__init__(self, path)
        self.article_id = article_id

    @classmethod
    def make( cls, article_id ):
        path = module.make_path(object='article_ref_list', article_id=article_id)
        return cls(path, article_id)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        return cls(path, article_id)

    def get_commands( self ):
        return [
            Command('parent', 'Parent', 'Open parent article', 'Ctrl+Backspace'),
            Command('add', 'Add ref', 'Create new reference', 'Ins'),
            ]

    def process_request( self, request ):
        if request.command_id == 'parent':
            return self.run_command_parent(request)
        if request.command_id == 'add':
            return self.run_command_add(request)
        if request.command_id == 'open':
            return request.make_response_object(RefSelector.make(self.article_id, ref_id=request.params.element_key))
        if request.command_id == 'delete':
            return self.run_element_command_delete(request)
        return ListObject.process_request(self, request)

    @db_session
    def run_command_parent( self, request ):
        rec = module.Article[self.article_id]
        return request.make_response_object(Article.from_rec(rec))

    def run_command_add( self, request ):
        with db_session:
            rec = module.ArticleRef(article=module.Article[self.article_id],
                                    path=json.dumps(request.params.target_path))
        return request.make_response_object(RefSelector.make(self.article_id, ref_id=rec.id))

    @db_session
    def run_element_command_delete( self, request ):
        ref_id = request.params.element_key
        module.ArticleRef[ref_id].delete()
        diff = ListDiff.delete(ref_id)
        return request.make_response_update(self.path, diff)

    @db_session
    def get_all_elements( self ):
        return map(self.rec2element, select(ref for ref in module.ArticleRef
            if ref.article==module.Article[self.article_id]) \
            .order_by(module.ArticleRef.id))

    def rec2element( self, rec ):
        commands = [
            Command('open', 'Open', 'Open reference selector'),
            Command('delete', 'Delete', 'Delete article reference', 'Del'),
            ]
        return Element(rec.id, [rec.id, rec.path], commands)


class UnwrapSelector(Object):

    iface = onwrap_object_selector_iface
    proxy_id = 'object_selector_unwrap'
    view_id = 'object_selector_unwrap'

    @classmethod
    def make( cls, base ):
        path = module.make_path(object='object_selector_unwrap')
        return cls(path, base)

    def __init__( self, path, base ):
        assert isinstance(base, Object), repr(base)
        Object.__init__(self, path)
        self._base = base

    def get_contents( self, **kw ):
        return Object.get_contents(self, base=self._base.get(), **kw)


class RefSelector(Object):

    iface = object_selector_iface
    proxy_id = 'object_selector'
    view_id = 'object_selector'

    def __init__( self, path, article_id, ref_id ):
        Object.__init__(self, path)
        self.article_id = article_id
        self.ref_id = ref_id

    @classmethod
    def make( cls, article_id, ref_id ):
        path = module.make_path(object='article_ref_selector', article_id=article_id, ref_id=ref_id)
        return cls(path, article_id, ref_id)

    @classmethod
    def from_path( cls, path ):
        article_id = path['article_id']
        ref_id = path['ref_id']
        return cls(path, article_id, ref_id)

    @db_session
    def get_contents( self, **kw ):
        if self.ref_id is None:
            target = None
        else:
            rec = module.ArticleRef[self.ref_id]
            target_path = json.loads(rec.path)
            target = module.run_resolve(target_path)
        return Object.get_contents(self, target=target, **kw)

    def process_request( self, request ):
        if request.command_id == 'choose':
            return self.run_command_choose(request)
        return Object.process_request(self, request)

    @db_session
    def run_command_choose( self, request ):
        target_path_str = json.dumps(request.params.target_path)
        if self.ref_id is None:
            rec = module.ArticleRef(article=module.Article[self.article_id],
                                    path=target_path_str)
        else:
            rec = module.ArticleRef[self.ref_id]
            rec.path = target_path_str
        commit()
        print 'Saved article#%d reference#%d path: %r' % (rec.article.id, rec.id, rec.path)
        ref_list_obj = ArticleRefList.make(article_id=self.article_id)
        list_elt_obj = ListObjectElement(ref_list_obj, rec.id)
        unwrapper_obj = UnwrapSelector.make(list_elt_obj)
        return request.make_response_object(unwrapper_obj)


class ArticleModule(PonyOrmModule):

    def __init__( self ):
        PonyOrmModule.__init__(self, MODULE_NAME)
        self.article_fields = dict(text=Required(unicode),
                                   refs=Set('ArticleRef'))

    def init_phase2( self ):
        self.Article = self.make_entity('Article', **self.article_fields)
        self.ArticleRef = self.make_entity('ArticleRef',
                                           article=Required(self.Article),
                                           path=Optional(str),
                                           )
        Article.register_class(self.Article)

    def resolve( self, path ):
        objname = path.get('object')
        if objname == 'article':
            return Article.from_path(path)
        if objname == 'article_ref_list':
            return ArticleRefList.from_path(path)
        if objname == 'article_ref_selector':
            return RefSelector.from_path(path)
        assert objname is None, repr(objname)  # Unknown object name
        return PonyOrmModule.resolve(self, path)

    def get_commands( self ):
        return [ModuleCommand('create', 'Create article', 'Create new article', 'Alt+A', self.name)]

    def run_command( self, request, command_id ):
        if command_id == 'create':
            return request.make_response_object(Article.make_new())
        return PonyOrmModule.run_command(self, request, command_id)

    def add_article_fields( self, **fields ):
        self.article_fields.update(fields)


module = ArticleModule()
