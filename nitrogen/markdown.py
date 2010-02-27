"""

Original taken from:
    http://gregbrown.co.nz/code/githib-flavoured-markdown-python-implementation/

I (mikeboers) have adapted it to work properly. It was only replacing newlines
at the very start of of a blob of text. I also removed the emphasis fixer
cause my markdown does it anyways, and this was screwing up flickr links.

The hash should really be salted.

Github flavoured markdown - ported from
http://github.github.com/github-flavored-markdown/

Usage:

    html_text = markdown(gfm(markdown_text))

(ie, this filter should be run on the markdown-formatted string BEFORE the markdown
filter itself.)

"""


from __future__ import absolute_import

import logging
import hashlib, re

from markdown import markdown as _markdown


log = logging.getLogger(__name__)


pre_extraction_re = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
italic_re = re.compile(r'(?! {4}|\t)\w+_\w+_\w[\w_]*')
newline_re = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE)
pre_insert_re = re.compile(r'{gfm-extraction-([0-9a-f]{40})\}')


def github_markdown(text):

    # Extract pre blocks
    extractions = {}
    def pre_extraction_callback(matchobj):
        sha1 = hashlib.sha1(matchobj.group(0)).hexdigest()
        extractions[sha1] = matchobj.group(0)
        return "{gfm-extraction-%s}" % sha1
    text = re.sub(pre_extraction_re, pre_extraction_callback, text)

    # prevent foo\_bar\_baz from ending up with an italic word in the middle
    # def italic_callback(matchobj):
    #     if len(re.sub(r'[^_]', '', matchobj.group(0))) > 1:
    #         return matchobj.group(0).replace('_', '\_')
    #     else:
    #         return matchobj.group(0)
    # text = re.sub(italic_re, italic_callback, text)

    # in very clear cases, let newlines become <br /> tags
    def newline_callback(matchobj):
        if len(matchobj.group(1)) == 1:
            return matchobj.group(0).rstrip() + '  \n'
        else:
            return matchobj.group(0)
    text = re.sub(newline_re, newline_callback, text)

    # Insert pre block extractions
    def pre_insert_callback(matchobj):
        return extractions[matchobj.group(1)]
    text = re.sub(pre_insert_re, pre_insert_callback, text)

    return text


def markdown(text, github=True):
    if github:
        return _markdown(github_markdown(text))
    return _markdown(text)



if __name__ == '__main__':
    print github_markdown('''hi\nthere
![Link text here](http://farm1.static.flickr.com/159/345009210_1f826cd5a1_m.jpg)
''')