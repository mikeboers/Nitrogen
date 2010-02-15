
# Bootstrap distribute.
import distribute_setup
distribute_setup.use_setuptools()


from setuptools import setup, find_packages

setup(

    name = "nitrogen",
    version = "0.1a.dev",
    packages = find_packages(),
    
    install_requires='''
        beaker
        beautifulsoup
        flup
        formalchemy
        lorem-ipsum-generator
        mako
        markdown
        minimock
        nose
        paste
        simplejson
        sqlalchemy
        webhelpers
        webob
        webtest
        pil
        
        # These are mine.
        multimap
        
    ''',
    
    include_package_data=True,
        
    author="Mike Boers",
    author_email="nitrogen@mikeboers.com",
    license="New BSD"
)
