"""nitrogen.view.defaults

This module contains default values for use with view environments. Currently
it only contains a `context` dict, which will be used as a starting point for
the `globals` attribute on a view environment.

It contains a number of functions and helpers that we tend to use all over the
place.

"""

# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = name[:name.rfind('.py')]
        name = (name[:-8] if name.endswith('__init__') else name).rstrip(os.path.sep)
        name = name.replace(os.path.sep, '.')
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)


import json

from markdown import markdown
import webhelpers.text
import webhelpers.html

from tools import urlify_name, clean_html


context = {}

context['repr'] = repr
context['sorted'] = sorted

context['json'] = json.dumps
context['markdown'] = lambda x: clean_html(markdown(x.encode('utf8'))).decode('utf8')
context['format_date'] = lambda d, f: (d.strftime(f) if d else '')
context['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
context['nl2br'] = lambda s: s.replace("\n", "<br />")

# context['textblob'] = textblob
# context['textblob_md'] = markdownblob

context['truncate'] = webhelpers.text.truncate
context['html'] = webhelpers.html.HTML

context['urlify_name'] = urlify_name
context['clean_html'] = clean_html
