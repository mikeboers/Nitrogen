
from . import EchoApp
from ..maprouter import MapRouter

def test_hexer():
    
    a = EchoApp('one')
    b = EchoApp('two')
    c = EchoApp('three')
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