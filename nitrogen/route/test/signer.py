
from . import EchoApp
from ..maprouter import MapRouter

def test_hexer():
    
    a = EchoApp('one')
    b = EchoApp('two')
    c = EchoApp('three')
    map = MapRouter('x')
    map.update(dict(a=a, b=b, c=c))
    hexer = Signer(map)
    
    url = hexer.url_for(x='a')
    print repr(url)
    pprint(hexer.route(url))
    # pprint(hexer.route('/a/whatever'))

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)