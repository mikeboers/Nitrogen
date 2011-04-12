import os

from datetime import datetime
from .app import *
from sqlalchemy import *

from nitrogen.cookies import parse_cookies
from nitrogen import forms

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
    
    title = forms.TextField(validators=[forms.validators.required()])
    post_time = forms.DateTimeField(validators=[forms.validators.required()])
    body = forms.MarkdownField()

crud = CRUD(
    Session=Session,
    render=render,
    model_class=Post,
    form_class=Form,
    partial='/crud/_post.html',
    partial_key='post'
)
router.register('/api', crud)

@router.register('')
@router.register('/')
@Request.application
def do_jquery(request):
    
    
    while table.select().count().scalar() < 5:

        session = Session()
        name = os.urandom(8).encode('hex')
        post = Post(
            title=name.title(),
            post_time=datetime.now(),
            body='Body of %s.' % name
        )
        session.add(post)
        session.commit()
        crud.commit(post, 'Auto-generated.')
    
    posts = Session().query(Post).all()
    return Response(render('/crud/index.html', posts=posts), as_html=True)
