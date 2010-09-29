

import logging
import re
import collections
import datetime

from multimap import MultiMap

import werkzeug as wz

from .request import Request
from .api import ApiRequest
from .app import build_inheritance_mixin_class

log = logging.getLogger(__name__)


as_api = ApiRequest.application


class CRUD(object):
    
    model_class = None
    form_class = None
    
    model_template=None
    model_view_kwargs={}
    model_view_key=None
    form_template='/form.html'
    form_view_kwargs={}
    form_view_key='form'
    render=None
    
    allow_create = True
    allow_update = True
    allow_delete = True
    allow_commit = True
    allow_revert = True
    
    def __init__(self, Session, **kwargs):
        
        self.Session = Session
        
        # For backwards compatibility.
        for oldkey, newkey in dict(
            partial='model_template',
            partial_kwargs='model_view_kwargs',
            partial_key='model_view_key',
        ).items():
            if oldkey in kwargs:
                kwargs[newkey] = kwargs.pop(oldkey)
        
        self.__dict__.update(kwargs)
    
    
    def _build_render_generic(name):
        template_attr = name + '_template'
        kwargs_attr = name + '_view_kwargs'
        key_attr = name + '_view_key'
        def render_object_generic(self, obj, **kwargs):
            if not self.render:
                raise ValueError('no render function')
            template = getattr(self, template_attr)
            kwargs.update(getattr(self, kwargs_attr))
            kwargs[getattr(self, key_attr)] = obj
            return self.render(template, **kwargs)
        return render_object_generic
    
    def _build_render(name):
        generic_attr = 'render_%s_generic' % name
        def render_object(self, obj, **kwargs):
            if hasattr(obj, 'render'):
                return getattr(obj, 'render')(**kwargs)
            return getattr(self, generic_attr)(obj, **kwargs)
        return render_object
            
    render_model_generic = _build_render_generic('model')
    render_model = _build_render('model')
    
    render_form_generic = _build_render_generic('form')
    render_form = _build_render('form')
    
    del _build_render_generic
    del _build_render
    
    @as_api
    def __call__(self, request):
        method = request.path.strip('/')
        if not method:
            request.error('no method given')
        handler = getattr(self, 'api_%s' % method, None)
        if not handler:
            request.error('bad method %r' % method)
        return handler(request)
        
    def versions_for(self, obj):
        """Return a list of (version, comment) tuples."""
        return []
    
    def commit(self, obj, comment=None):
        """Commit the state of the given object."""
        pass
        
    def revert(self, obj, version):
        """Revert the given object to the state from the given version."""
        pass
    
    def api_getForm(self, request):
        
        id_ = request.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            request.error("bad id")
        
        # Get a version > 0, or None.
        version = int(request.get('version', 0)) or None
        
        s = self.Session()
        if id_:
            obj = s.query(self.model_class).get(id_)
            if not obj:
                raise ApiError("could not find object %d" % id_)
            
            # Apply requested version data.
            if version and self.allow_revert:
                self.revert(obj, version)
                
            form = self.form_class(obj=obj)
        else:
            obj = None
            form = self.form_class()
        
        return self.get_form_response(obj, form)
        
        
    def get_form_response(self, obj, form):
        return dict(
            form=self.render_form(form),
            versions=self.versions_for(obj) if obj and self.allow_revert else None,
        )
    
    def api_save(self, request, commit=True):
        
        response = {}
        
        id_ = request.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            request.error("bad id")
        
        s = self.Session()
        model = None  
        if id_:
            model = s.query(self.model_class).get(id_)
            if not model:
                request.error("could not find object %d" % id_)
        else:
            model = self.model_class()
        form = self.form_class(MultiMap(request.form))
        response['valid'] = valid = form.validate()
        
        if not valid:
            res = self.get_form_response(model, form)
            res['valid'] = False
            return res
        
        
        form.populate_obj(model)
        
        # This "commit" refers to the database, as this method is overloaded
        # to provide preview functionality as well.
        if commit:
            
            if not model.id: 
                s.add(model)
            s.commit()
            response['id'] = model.id
            
            if self.allow_commit and request.get('__do_commit_version'):
                commit_message = request.get('__version_comment', '')
                self.commit(model, commit_message)
        
        data = {}
        for key in request.form:
            m = re.match(r'^partial_kwargs\[(.+?)\]$', key)
            if m:
                data[m.group(1)] = request[key]
        
        response['html'] = self.render_model(model, **data)
        
        # Must explicity roll back the changes we have made otherwise
        # the database will remain locked.
        if not commit:
            s.rollback()
        
        return response
    
    def api_preview(self, request):
        return self.api_save(request, commit=False)

    def api_delete(self, request):
        id_ = request['id']
        s = self.Session()
        obj = s.query(self.model_class).get(id_)
        if not obj:
            raise ApiError("could not find object %d" % id_)
        obj.delete()
        s.commit()
    # 
    # def handle_order(self, request):
    #     order = [int(x) for x in request['order'].split(',')]
    # 
    #     # Remove dummy (zero) ids.
    #     order = filter(None, order)
    # 
    #     # Grab all of the items that we are dealing with.
    #     items = self.session.query(self.model_class).filter(self.model_class.id.in_(order)).all()
    # 
    #     # Make sure that we have them all.
    #     if len(items) != len(order):
    #         raise ApiError("Could not find all the items.")
    # 
    #     id_to_items = dict((item.id, item) for item in items)
    #     order_ids = list(sorted(item.order_id for item in items))
    # 
    #     for i, id_ in enumerate(order):
    #         item = id_to_items[id_]
    #         item.order_id = order_ids[i]
    # 
    #     self.session.commit()


class CRUDAppMixin(object):
    
    build_crud_class = lambda self: build_inheritance_mixin_class(self.__class__, CRUD)
    CRUD = wz.cached_property(build_crud_class, name='CRUD')
    
    class CRUDMixin(object):
        
        @wz.cached_property
        def commits_by_id(self):
            return collections.defaultdict(list)
            
        def versions_for(self, obj):
            id = obj.id
            versions = []
            for i, raw in enumerate(self.commits_by_id[id]):
                comment = raw['comment'].strip()
                versions.append((i + 1, raw['commit_time'].ctime() + (': ' if comment else '') + comment))
            if versions:
                versions.append((0, '< current >'))
            return versions
        
        def commit(self, obj, comment=None):
            id = obj.id
            data = obj.todict()
            log.debug('COMMIT %r to %r: %r' % (id, data, comment))
            self.commits_by_id[id].append(dict(
                data=data,
                comment=comment,
                commit_time=datetime.datetime.now()
            ))
            
        def revert(self, obj, version):
            for key, value in self.commits_by_id[obj.id][version - 1]['data'].iteritems():
                setattr(obj, key, value)

    
    def export_to(self, map):
        super(CRUDAppMixin, self).export_to(map)
        map['CRUD'] = self.CRUD
    
    
    