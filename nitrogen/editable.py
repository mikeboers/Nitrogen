
from .api import as_api, ApiError, ApiKeyError

"""

how it was hooked up before
ModelAdapter(name='newspost',
     model=news_model.NewsPost,
     form=news_model.form,
     partial='news/post.tpl',
     partial_key='post'),
     
"""

class Editable(object):
    
    def __init__(self, session, render, model, form, partial, partial_key,
        keys=None, table=None, before_save=None):
        
        self.session = session
        self.render = render
        
        self.model = model
        self.form = form
        self.partial = partial
        self.partial_key = partial_key
        self.table = table or model.__table__
        self.keys = keys or [col.name for col in self.table.columns]
        
        self.before_save = before_save

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

        obj = self.session.query(self.model).get(id_)

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

        if id_:
            obj = self.session.query(self.model).get(id_)
            if not obj:
                raise ApiError("could not find object %d" % id_)
            form = self.form.bind(obj)
        else:
            form = self.form.bind(session=self.session)

        res['form'] = form.render()

    def handle_submit_form(self, req, res):

        id_ = req.get('id')
        try:
            id_ = int(id_) if id_ else None
        except:
            raise ApiError("Bad id.")

        model = None  
        if id_:
            model = self.session.query(self.model).get(id_)
            if not model:
                raise ApiError("could not find object %d" % id_)
            form = self.form.bind(model)
        else:
            form = self.form.bind(session=self.session)

        form = form.bind(data=req)
        
        try:
            res['valid'] = valid = form.validate()
        except KeyError as e:
            raise ApiKeyError(e.args[0])
        
        if not valid:
            res['form'] = form.render()
        else:
            form.sync()
            if not model:
                model = form.model
                self.session.add(model)
            if self.before_save:
                self.before_save(req, model)
            self.session.commit()

            res['id'] = model.id
            res['partial'] = self.render(self.partial, **{self.partial_key: model});

    def handle_delete(self, req, res):
        id_ = req['id']
        obj = self.session.query(self.model).get(id_)
        if not obj:
            raise ApiError("could not find object %d" % id_)
        obj.delete()
        self.session.commit()

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