
from .tools import Router, TestApp
from .maprouter import MapRouter

class Hexer(Router):
    
    def __init__(self, app):
        self.app = app
    
    def route_step(self, path):
        try:
            path = path[1:].decode('hex')
        except:
            pass
        return self.app, path, {}
    
    def generate_step(self, data):
        return '', self.app
    
    def modify_path(self, path):
        print 'Hexer.modify_path', path
        return '/' + path.encode('hex')


def test_hexer():
    
    a = TestApp('one')
    b = TestApp('two')
    c = TestApp('three')
    map = MapRouter('x')
    map.update(dict(a=a, b=b, c=c))
    
    # print map.route('/a')
    hexer = Hexer(map)
    
    print repr(map.url_for(x='a'))
    
    url = hexer.url_for(x='a')
    print repr(url)
    
    print hexer.route(url)

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)