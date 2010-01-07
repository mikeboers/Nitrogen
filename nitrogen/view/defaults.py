"""nitrogen.view.defaults

This module contains default values for use with view environments. Currently
it only contains a `context` dict, which will be used as a starting point for
the `globals` attribute on a view environment.

It contains a number of functions and helpers that we tend to use all over the
place.

"""


import json
import pprint

import webhelpers.text
import webhelpers.html
from markdown import markdown

from .tools import urlify_name, clean_html
from ..markdown import github_markdown

context = {}

context['repr'] = repr
context['sorted'] = sorted

context['json'] = json.dumps
context['markdown'] = lambda x: clean_html(markdown(github_markdown(x)))
context['format_date'] = lambda d, f: (d.strftime(f) if d else '')
context['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
context['nl2br'] = lambda s: s.replace("\n", "<br />")

context['pformat'] = pprint.pformat

# context['textblob'] = textblob
# context['textblob_md'] = markdownblob

context['truncate'] = webhelpers.text.truncate
context['html'] = webhelpers.html.HTML

context['urlify_name'] = urlify_name
context['clean_html'] = clean_html


def test_markdown():
    print 'Markdown of "**bold**":'
    print markdown('**bold**')
    
    print markdown(github_markdown('''hi\nthere
![Link text here](http://farm1.static.flickr.com/159/345009210_1f826cd5a1_m.jpg)
'''))


if __name__ == '__main__':
    from .. import test
    test.run()