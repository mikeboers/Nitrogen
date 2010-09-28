

import logging
import re

from multimap import MultiMap

from .request import Request
from .api import ApiRequest


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
        method = request['method']
        handler = getattr(self, 'handle_%s' % method, None)
        if not handler:
            request.error('no api method %r' % method)
        return handler(request)

    # def handle_get(self, request, response):
    #     
    #     id_ = int(request['id'])
    #     
    #     s = self.Session()
    #     obj = s.query(self.model_class).get(id_)
    # 
    #     if not obj:
    #         raise ApiError("could not find object %d" % id_)
    # 
    #     for key in self.keys:
    #         response[key] = getattr(obj, key)

    def handle_get_form(self, request):

        id_ = request.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            request.error("bad id")
        
        s = self.Session()
        if id_:
            obj = s.query(self.model_class).get(id_)
            if not obj:
                raise ApiError("could not find object %d" % id_)
            form = self.form_class(obj=obj)
        else:
            form = self.form_class()

        return dict(form=self.render_form(form))

    def handle_submit_form(self, request, commit=True):
        
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
            response['form'] = self.render_form(form)
        
        else:
            form.populate_obj(model)
            
            if commit:
                if not model.id: 
                    s.add(model)
                s.commit()
                response['id'] = model.id
                
            data = {}
            for key in request.form:
                m = re.match(r'^partial_kwargs\[(.+?)\]$', key)
                if m:
                    data[m.group(1)] = request[key]
            
            response['partial'] = self.render_model(model, **data)
            
            # Must explicity roll back the changes we have made otherwise
            # the database will remain locked.
            if not commit:
                s.rollback()
        
        return response
    
    def handle_preview(self, request):
        return self.handle_submit_form(request, commit=False)

    def handle_delete(self, request):
        id_ = request['id']
        s = self.Session()
        obj = s.query(self.model_class).get(id_)
        if not obj:
            raise ApiError("could not find object %d" % id_)
        obj.delete()
        s.commit()

    def handle_order(self, request):
        order = [int(x) for x in request['order'].split(',')]

        # Remove dummy (zero) ids.
        order = filter(None, order)

        # Grab all of the items that we are dealing with.
        items = self.session.query(self.model_class).filter(self.model_class.id.in_(order)).all()

        # Make sure that we have them all.
        if len(items) != len(order):
            raise ApiError("Could not find all the items.")

        id_to_items = dict((item.id, item) for item in items)
        order_ids = list(sorted(item.order_id for item in items))

        for i, id_ in enumerate(order):
            item = id_to_items[id_]
            item.order_id = order_ids[i]

        self.session.commit()