"""Class to assist in pagination.

Examples:

    >>> data = range(100)
    >>> pager = Pager(data)
    
    >>> list(pager)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    >>> pager.page = 2
    >>> list(pager)
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    
    >>> pager.pagecount
    10
    
    >>> pager.render()
    u'<a href="1">&lt;&lt;</a><a href="1">1</a>[2]<a href="3">3</a><a href="4">4</a><a href="5">5</a>..<a href="9">9</a><a href="10">10</a><a href="3">&gt;&gt;</a>'
    
    >>> pager.rendertest()
    u'1 << 1 1 [2] 3 3 4 4 5 5 .. 9 9 10 10 3 >>'
    
    >>> pager.page = 5
    >>> pager.rendertest()
    u'4 << 1 1 2 2 3 3 4 4 [5] 6 6 7 7 8 8 9 9 10 10 6 >>'

"""

from __future__ import division

import re

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

from webhelpers.html import HTML

class Pager(object):
    
    def __init__(self, data, page=1, count=None, per_page=10):
        self.data = data
        self.page = page
        
        if count is None:
            self.data = list(data)
            self.count = len(self.data)
        else:
            self.count = count
        
        self.per_page = per_page
        self.page_radius = 3
    
    def __iter__(self):
        for x in self.data[(self.page - 1) * self.per_page: self.page * self.per_page]:
            yield x
    
    @property
    def pagecount(self):
        return self.count // self.per_page
    
    def render(self, format='%d'):
        chunks = []
        
        def href(page):
            return format % page
        
        def link(page):
            if page == self.page:
                chunks.append('[%d]' % page)
            else:
                chunks.append(HTML.tag('a', str(page), href=href(page)))
        
        if self.page > 1:
            # Start
            chunks.append(HTML.tag('a', '<<', href=href(1)))
            # Previous page
            chunks.append(HTML.tag('a', '<', href=href(self.page - 1)))
        
        # First one
        link(1)
        
        # The seperator if it should be there
        if self.page > self.page_radius + 2:
            chunks.append('..')
        
        # The middle ones.
        for i in range(max(2, self.page - 3), min(self.pagecount, self.page + self.page_radius + 1)):
            link(i)
        
        # The end sepeartor
        if self.pagecount - self.page > self.page_radius + 1:
            chunks.append('..')
        
        # The last one.
        if self.pagecount - self.page > self.page_radius:
            link(self.pagecount)
        
        if self.page < self.pagecount:
            # Next page
            chunks.append(HTML.tag('a', '>', href=href(self.page + 1)))
            chunks.append(HTML.tag('a', '>>', href=href(self.pagecount)))
        
        return ''.join(chunks)
    
    def rendertest(self, format='%d'):
        """Strips out all of the html."""
        stuff = re.sub(r'(<[^>]+?>)+', ' ', self.render(format)).strip()
        stuff = stuff.replace('&lt;', '<')
        stuff = stuff.replace('&gt;', '>')
        return stuff

if __name__ == '__main__':
    from .test import run
    run()