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
    u'<span class="pager"><span class="current">1</span><a href="2" title="Go to page 2">2</a><a href="3" title="Go to page 3">3</a><a href="4" title="Go to page 4">4</a>..<a href="10" title="Go to page 10">10</a><a class="next" href="2" title="Go to page 2">Next</a></span>'
    
    >>> pager.current_wrapper = '[%d]'
    >>> pager.rendertest()
    u'[1] 2 3 4 .. 10 Next'
    
    >>> pager.page = 2
    >>> pager.rendertest()
    u'Prev 1 [2] 3 4 5 .. 10 Next'
    
    >>> pager.page = 5
    >>> pager.rendertest()
    u'Prev 1 2 3 4 [5] 6 7 8 .. 10 Next'
    
    >>> pager.render()
    u'<span class="pager"><a class="prev" href="4" title="Go to page 4">Prev</a><a href="1" title="Go to page 1">1</a><a href="2" title="Go to page 2">2</a><a href="3" title="Go to page 3">3</a><a href="4" title="Go to page 4">4</a><span class="current">[5]</span><a href="6" title="Go to page 6">6</a><a href="7" title="Go to page 7">7</a><a href="8" title="Go to page 8">8</a>..<a href="10" title="Go to page 10">10</a><a class="next" href="6" title="Go to page 6">Next</a></span>'
    
    >>> pager.page = 6
    >>> pager.rendertest()
    u'Prev 1 .. 3 4 5 [6] 7 8 9 10 Next'
    
    >>> pager.page = 9
    >>> pager.rendertest()
    u'Prev 1 .. 6 7 8 [9] 10 Next'
    
    >>> pager.page = 10
    >>> pager.rendertest()
    u'Prev 1 .. 7 8 9 [10]'
    
    >>> pager.page = 1
    >>> pager.next_token = 'Next &laquo'
    >>> pager.render()
    u'<span class="pager"><span class="current">[1]</span><a href="2" title="Go to page 2">2</a><a href="3" title="Go to page 3">3</a><a href="4" title="Go to page 4">4</a>..<a href="10" title="Go to page 10">10</a><a class="next" href="2" title="Go to page 2">Next &laquo</a></span>'
    
"""


from __future__ import division

import re
from math import ceil

from webhelpers.html import literal, HTML


class Pager(object):
    
    WRAPPER_CLASS = 'pager'
    PREV_CLASS = 'prev'
    CURRENT_CLASS = 'current'
    NEXT_CLASS = 'next'
    
    PREV_TOKEN = 'Prev'
    SEPERATOR = '..'
    CURRENT_WRAPPER = '%d'
    NEXT_TOKEN = 'Next'
    
    TITLE_FORMAT = 'Go to page %d'
    HREF_FORMAT = '%d'
    
    def __init__(self, data=None,
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
        
        for k in '''wrapper_class prev_class current_class next_class
                    prev_token seperator current_wrapper next_token title_format'''.split():
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
                chunks.append(HTML.tag('span', literal(self.current_wrapper % page), class_=self.current_class))
            else:
                chunks.append(HTML.tag('a', str(page), title=self.title_format % page, href=href(page)))
        
        # Previous page
        if self.page > 1:
            chunks.append(HTML.tag('a', literal(self.prev_token),  title=self.title_format % (self.page - 1), href=href(self.page - 1), class_=self.prev_class))
        
        # First one
        link(1)
        
        # The first seperator.
        if self.page - self.page_radius > 2:
            chunks.append(literal(self.seperator))
        
        # The middle ones.
        for i in range(
            max(2, self.page - self.page_radius),
            min(self.page_count, self.page + self.page_radius + 1)
        ):
            link(i)
        
        # The end seperator
        if self.page_count - self.page > self.page_radius + 1:
            chunks.append(literal(self.seperator))
        
        # The last one.
        if self.page_count > 1:
            link(self.page_count)
        
        if self.page < self.page_count:
            # Next page
            chunks.append(HTML.tag('a', literal(self.next_token), title=self.title_format % (self.page + 1), href=href(self.page + 1), class_=self.next_class))
        
        return unicode(HTML.tag('span', *chunks, class_=self.wrapper_class))
    
    def _render_href(self, page):
        return self._href_format % page
    
    def rendertest(self, format='%d'):
        """Strips out all of the html."""
        stuff = re.sub(r'(<[^>]+?>)+', ' ', self.render(format)).strip()
        stuff = stuff.replace('&lt;', '<')
        stuff = stuff.replace('&gt;', '>')
        return stuff
    
    pager = render

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)