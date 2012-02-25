import os
from datetime import datetime

import sqlalchemy as sa

from nitrogen.cookies import parse_cookies
from nitrogen import forms

from . import *
from ..main import CRUD


class Post(app.Base):
    __tablename__ = 'example_posts'
    
    id = sa.Column(sa.Integer, primary_key=True)
    title = sa.Column(sa.Unicode, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False)
    body = sa.Column(sa.Unicode, nullable=False)


Post.__table__.create(checkfirst=True)


class Form(app.Form):
    
    title = forms.TextField(validators=[forms.validators.required()])
    created_at = forms.DateTimeField(validators=[forms.validators.required()])
    body = forms.MarkdownField()


crud = route('/api', CRUD(
    Session=Session,
    render=render,
    model_class=Post,
    form_class=Form,
    partial='/crud/_post.html',
    partial_key='post'
))

@route('/')
def do_crud(request):
    
    session = Session()
    
    while session.query(Post).count() < 5:

        name = os.urandom(8).encode('hex')
        post = Post(
            title=name.title(),
            created_at=datetime.utcnow(),
            body='Body of %s.' % name
        )
        session.add(post)
        session.commit()
        crud.commit(post, 'Auto-generated.')
    
    posts = session.query(Post).all()
    return Response(render('/crud/index.html', posts=posts))
