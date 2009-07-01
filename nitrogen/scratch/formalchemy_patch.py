
import sys
sys.path.append('lib')

from sqlalchemy import *
from elixir import *

import formalchemy as fa
# import formalchemy.fields

if __name__ == '__main__':
    
    metadata.bind = 'sqlite://'
    metadata.bind.echo = False

    class Test(Entity):
        id = Field(Integer, primary_key=True)
        string = Field(String)
        text = Field(Text)
        bool = Field(Boolean)

    setup_all(True)




    print cls.name

    fs = fa.FieldSet(Test)

    print fs.render()