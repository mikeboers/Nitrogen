

import logging
import re

from multimap import MultiMap

from ..request import Request
from ..api import as_api


log = logging.getLogger(__name__)


class CRUD(object):
    
    def __init__(self, Session, render, model_class, form_class, partial, partial_key,
        partial_kwargs=None, keys=None, table=None, form_template='_form.html.mako'):
        
        self.Session = Session
        self.render = render
        
        self.model = self.model_class = model_class
        self.form = self.form_class = form_class
        
        self.partial = partial
        self.partial_key = partial_key
        self.partial_kwargs = partial_kwargs or {}
        
        self.table = table or model_class.__table__
        self.keys = keys or [c.name for c in self.table.c]
        self.form_template = form_template
    
    @as_api
    def __call__(self, req, res):
        with res:
            method = req['method']
            handler = getattr(self, 'handle_%s' % method, None)
            if not handler:
                raise ApiError('no api method %r' % method)
            handler(req, res)
        return res

    def handle_get(self, req, res):
        
        id_ = int(req['id'])
        
        s = self.Session()
        obj = s.query(self.model).get(id_)

        if not obj:
            raise ApiError("could not find object %d" % id_)

        for key in self.keys:
            res[key] = getattr(obj, key)

    def handle_get_form(self, req, res):

        id_ = req.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            raise ApiError("bad id")
        
        s = self.Session()
        if id_:
            obj = s.query(self.model).get(id_)
            if not obj:
                raise ApiError("could not find object %d" % id_)
            form = self.form_class(obj=obj)
        else:
            form = self.form_class()

        res['form'] = self.render(self.form_template, form=form)

    def handle_submit_form(self, req, res):

        id_ = req.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            raise ApiError("Bad id.")
        
        s = self.Session()
        model = None  
        if id_:
            model = s.query(self.model).get(id_)
            if not model:
                raise ApiError("could not find object %d" % id_)
        else:
            model = self.model()
        form = self.form_class(MultiMap(req))
        res['valid'] = valid = form.validate()
        
        if not valid:
            res['form'] = self.render(self.form_template, form=form)
        else:
            form.populate_obj(model)
            if not model.id: 
                s.add(model)
            s.commit()

            res['id'] = model.id
            data = {}
            for key in req:
                m = re.match(r'^partial_kwargs\[(.+?)\]$', key)
                if m:
                    data[m.group(1)] = req[key]
            data[self.partial_key] = model
            data.update(self.partial_kwargs)
            res['partial'] = self.render(self.partial, **data)

    def handle_delete(self, req, res):
        id_ = req['id']
        s = self.Session()
        obj = s.query(self.model).get(id_)
        if not obj:
            raise ApiError("could not find object %d" % id_)
        obj.delete()
        s.commit()

    def handle_order(self, req, res):
        order = [int(x) for x in req['order'].split(',')]

        # Remove dummy (zero) ids.
        order = filter(None, order)

        # Grab all of the items that we are dealing with.
        items = self.session.query(self.model).filter(self.model.id.in_(order)).all()

        # Make sure that we have them all.
        if len(items) != len(order):
            raise ApiError("Could not find all the items.")

        id_to_items = dict((item.id, item) for item in items)
        order_ids = list(sorted(item.order_id for item in items))

        for i, id_ in enumerate(order):
            item = id_to_items[id_]
            item.order_id = order_ids[i]

        self.session.commit()