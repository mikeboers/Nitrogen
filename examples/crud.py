import os

from datetime import datetime
from .app import *
from sqlalchemy import *

from nitrogen.webio.cookies import parse_cookies
from nitrogen import forms
from nitrogen.crud import CRUD

crud_app = router = ReRouter()


table = Table('crud', metadata, 
    Column('id', Integer, primary_key=True),
    Column('title', Unicode, nullable=False),
    Column('post_time', DateTime, nullable=False),
    Column('body', Unicode, nullable=False),
)

metadata.create_all()

class Post(Base):
    __table__ = table

FormBase = Form
class Form(FormBase):
    
    title = forms.TextField()
    post_time = forms.DateTimeField()
    body = forms.MarkdownField()


router.register('/api', CRUD(
    Session=Session,
    render=render,
    model_class=Post,
    form_class=Form,
    partial='/crud/_post.html',
    partial_key='post'
))

@router.register('')
@router.register('/')
@Request.application
def do_jquery(request):
    
    
    while table.select().count().scalar() < 5:

        session = Session()
        name = os.urandom(8).encode('hex')
        session.add(Post(
            title=name.title(),
            post_time=datetime.now(),
            body='Body of %s.' % name
        ))
        session.commit()
    
    posts = Session().query(Post).all()
    return Response(render('/crud/index.html', posts=posts), as_html=True)
