
import sys
sys.path.append('lib')

from sqlalchemy import *
from elixir import *
import formalchemy as forms

metadata.bind = 'sqlite://'
metadata.bind.echo = False

class BlogPost(Entity):
    id = Field(Integer, primary_key=True)
    title = Field(String)
    image_uri = Field(String)
    body = Field(Text)

setup_all(True)

fs = forms.FieldSet(BlogPost)
print fs.render()