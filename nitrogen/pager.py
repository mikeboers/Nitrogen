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
    u'<span class="pager"><span class="current">[1]</span><a href="2">2</a><a href="3">3</a><a href="4">4</a>..<a href="10">10</a><a class="next" href="2">&gt;</a><a class="last" href="10">&gt;&gt;</a></span>'
    
    >>> pager.rendertest()
    u'[1] 2 3 4 .. 10 > >>'
    
    >>> pager.page = 2
    >>> pager.rendertest()
    u'<< < 1 [2] 3 4 5 .. 10 > >>'
    
    >>> pager.page = 5
    >>> pager.rendertest()
    u'<< < 1 2 3 4 [5] 6 7 8 .. 10 > >>'
    
    >>> pager.render()
    u'<span class="pager"><a class="first" href="1">&lt;&lt;</a><a class="prev" href="4">&lt;</a><a href="1">1</a><a href="2">2</a><a href="3">3</a><a href="4">4</a><span class="current">[5]</span><a href="6">6</a><a href="7">7</a><a href="8">8</a>..<a href="10">10</a><a class="next" href="6">&gt;</a><a class="last" href="10">&gt;&gt;</a></span>'
    
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
from math import ceil

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

from webhelpers.html import HTML

class Pager(object):
    
    WRAPPER_CLASS = 'pager'
    FIRST_CLASS = 'first'
    PREV_CLASS = 'prev'
    CURRENT_CLASS = 'current'
    NEXT_CLASS = 'next'
    LAST_CLASS = 'last'
    
    FIRST_TOKEN = '<<'
    PREV_TOKEN = '<'
    SEPERATOR = '..'
    CURRENT_WRAPPER = '[%d]'
    NEXT_TOKEN = '>'
    LAST_TOKEN = '>>'
    
    HREF_FORMAT = '%d'
    
    def __init__(self, data,
        page=1,
        count=None,
        per_page=10,
        page_radius=3,
        href_format=HREF_FORMAT
    ):
        self.data = data
        
        if count is None:
            self.data = list(data)
            self.count = len(self.data)
        else:
            self.count = count
        
        self.per_page = per_page
        
        # Need to set this after the count/per_page are set cause ranges must be checked.
        self.page = page
        
        self.page_radius = page_radius
        
        for k in '''wrapper_class first_class prev_class current_class next_class last_class
                    first_token prev_token seperator current_wrapper next_token last_token'''.split():
            setattr(self, k, getattr(self, k.upper()))
        
        self.href_format = href_format
    
    def __iter__(self):
        for x in self.data[(self.page - 1) * self.per_page: self.page * self.per_page]:
            yield x
    
    @property
    def page(self):
        return self._page
    
    @page.setter
    def page(self, v):
        self._page = max(1, min(self.page_count, int(v)))
    
    @property
    def page_count(self):
        return int(ceil(self.count / self.per_page))
    
    def render(self, href_format=None):
        chunks = []
        
        self._href_format = href_format or self.href_format
        def href(page):
            return self._render_href(page)
        
        def link(page):
            if page == self.page:
                chunks.append(HTML.tag('span', self.current_wrapper % page, class_=self.current_class))
            else:
                chunks.append(HTML.tag('a', str(page), href=href(page)))
        
        if self.page > 1:
            # Start
            chunks.append(HTML.tag('a', self.first_token, href=href(1), class_=self.first_class))
            # Previous page
            chunks.append(HTML.tag('a', self.prev_token, href=href(self.page - 1), class_=self.prev_class))
        
        # First one
        link(1)
        
        # The first seperator.
        if self.page - self.page_radius > 2:
            chunks.append(self.seperator)
        
        # The middle ones.
        for i in range(
            max(2, self.page - self.page_radius),
            min(self.page_count, self.page + self.page_radius + 1)
        ):
            link(i)
        
        # The end seperator
        if self.page_count - self.page > self.page_radius + 1:
            chunks.append(self.seperator)
        
        # The last one.
        if self.page_count > 1:
            link(self.page_count)
        
        if self.page < self.page_count:
            # Next page
            chunks.append(HTML.tag('a', self.next_token, href=href(self.page + 1), class_=self.next_class))
            chunks.append(HTML.tag('a', self.last_token, href=href(self.page_count), class_=self.last_class))
        
        return unicode(HTML.tag('span', *chunks, class_=self.wrapper_class))
    
    def _render_href(self, page):
        return self._href_format % page
    
    def rendertest(self, format='%d'):
        """Strips out all of the html."""
        stuff = re.sub(r'(<[^>]+?>)+', ' ', self.render(format)).strip()
        stuff = stuff.replace('&lt;', '<')
        stuff = stuff.replace('&gt;', '>')
        return stuff

if __name__ == '__main__':
    from .test import run
    run()