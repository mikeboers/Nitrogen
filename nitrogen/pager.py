"""Class to assist in pagination.

Examples:

    >>> data = range(100)
    >>> pager = Pager(data)
    
    >>> list(pager)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    >>> pager.page = 2
    >>> list(pager)
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    
    >>> pager.page_count
    10
    
    >>> pager = Pager(range(100))
    >>> pager.render()
    u'[1]<a href="2">2</a><a href="3">3</a><a href="4">4</a>..<a href="10">10</a><a href="2">&gt;</a><a href="10">&gt;&gt;</a>'
    
    >>> pager.rendertest()
    u'[1] 2 3 4 .. 10 > >>'
    
    >>> pager.page = 2
    >>> pager.rendertest()
    u'<< < 1 [2] 3 4 5 .. 10 > >>'
    
    >>> pager.page = 5
    >>> pager.rendertest()
    u'<< < 1 2 3 4 [5] 6 7 8 .. 10 > >>'
    
    >>> pager.page = 6
    >>> pager.rendertest()
    u'<< < 1 .. 3 4 5 [6] 7 8 9 10 > >>'
    
    >>> pager.page = 9
    >>> pager.rendertest()
    u'<< < 1 .. 6 7 8 [9] 10 > >>'
    
    >>> pager.page = 10
    >>> pager.rendertest()
    u'<< < 1 .. 7 8 9 [10]'
    
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
    def page_count(self):
        return self.count // self.per_page
    
    def render(self, format='%d'):
        chunks = []
        
        self.href_format = format
        def href(page):
            return self._render_href(page)
        
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
        
        # The first seperator.
        if self.page - self.page_radius > 2:
            chunks.append('..')
        
        # The middle ones.
        for i in range(
            max(2, self.page - self.page_radius),
            min(self.page_count, self.page + self.page_radius + 1)
        ):
            link(i)
        
        # The end seperator
        if self.page_count - self.page > self.page_radius + 1:
            chunks.append('..')
        
        # The last one.
        if self.page_count > 1:
            link(self.page_count)
        
        if self.page < self.page_count:
            # Next page
            chunks.append(HTML.tag('a', '>', href=href(self.page + 1)))
            chunks.append(HTML.tag('a', '>>', href=href(self.page_count)))
        
        return ''.join(chunks)
    
    def _render_href(self, page):
        return self.href_format % page
    
    def rendertest(self, format='%d'):
        """Strips out all of the html."""
        stuff = re.sub(r'(<[^>]+?>)+', ' ', self.render(format)).strip()
        stuff = stuff.replace('&lt;', '<')
        stuff = stuff.replace('&gt;', '>')
        return stuff

if __name__ == '__main__':
    from .test import run
    run()