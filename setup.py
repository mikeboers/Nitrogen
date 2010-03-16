
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
        flup
        webob
        
        # Going to be replacing this with wtform soon.
        formalchemy
        
        mako
        markdown
        lorem-ipsum-generator
        
        # Testing
        nose
        minimock
        webtest
        
        sqlalchemy
        
        # This is only for the pager and some functions in the templates.
        webhelpers
        
        # For the imgsizer.
        pil
        
        # These are mine.
        multimap
        
    ''',
    
    include_package_data=True,
        
    author="Mike Boers",
    author_email="nitrogen@mikeboers.com",
    license="New BSD"
)
