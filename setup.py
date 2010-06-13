
# Bootstrap distribute.
import distribute_setup
distribute_setup.use_setuptools()


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
        
        mako
        markdown
        lorem-ipsum-generator
        
        sqlalchemy
        
        # This is only for the pager and some functions in the templates.
        webhelpers
        
        # These are mine.
        multimap
        
    ''',
    
    extras_require=dict(
        imgsizer=['pil'],
        testing='''
            nose
            webtest
            # minimock
            ''',
        
    ),
    
    include_package_data=True,
        
    author="Mike Boers",
    author_email="nitrogen@mikeboers.com",
    license="New BSD"
)
