
from setuptools import setup, find_packages

setup(

    name = "nitrogen",
    version = "0.1a.dev",
    packages = find_packages(),
    
    install_requires='''
        # core
        flup
        webob
        werkzeug
        beaker
        
        mako
        markdown
        sqlalchemy
        
        # This is only for the pager and some functions in the templates.
        webhelpers
        
        # These are mine.
        multimap
        pytomcrypt
        
        wtforms
        paste
        pil
        
        pygments
        jsmin

        # imgsizer
        pil
    ''',
    
    extras_require=dict(
        testing='''
            nose
            webtest
            # minimock
            ''',
        
    ),
    
    include_package_data=True,
        
    author="Mike Boers",
    author_email="nitrogen@mikeboers.com",
    license="BSD-3"
)
