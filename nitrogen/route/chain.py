
from webstar import Router


def Chain(routes):
    router = Router()
    def append(route):
        router.register('', route)
    router.append = append
    for route in routes:
        router.register('', route)
    return router

