
from setuptools import setup, find_packages

setup(

    name = "nitrogen",
    version = "0.1a.dev",
    packages = find_packages(),
    
    install_requires='''
        # core
        webob
        werkzeug>=0.8.3
        beaker
        paste
        
        sqlalchemy
        
        mako>=0.4.2
        markdown>=2.1.1
        pygments>=1.4
        
        # This is only for the pager and some functions in the templates.
        webhelpers
        
        # These are mine.
        multimap
        pytomcrypt
        
        wtforms
        
        jsmin

        # imgsizer
        pil
    ''',
    
    extras_require=dict(
        testing='''
            nose
            webtest
            ''',
        
    ),
    
    include_package_data=True,
        
    author="Mike Boers",
    author_email="nitrogen@mikeboers.com",
    license="BSD-3"
)
