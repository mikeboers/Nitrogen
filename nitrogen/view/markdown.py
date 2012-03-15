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

import os
import logging
import re
import cgi

import markdown as _markdown
from markdown import Markdown
from markdown.extensions.codehilite import CodeHilite, CodeHiliteExtension

log = logging.getLogger(__name__)


class Nl2BrExtension(_markdown.Extension):
    
    class Preprocessor(_markdown.preprocessors.Preprocessor):
        
        pre_extraction_re = re.compile(r'<pre>.*?</pre>', re.MULTILINE | re.DOTALL)
        newline_re = re.compile(r'^[\w\<][^\n]*(\n+)', re.MULTILINE)
        pre_insert_re = re.compile(r'{nl2br-([0-9a-f]{32})\}')
        
        def run(self, lines):
            
            text = '\n'.join(lines)
            
            # Extract pre blocks
            extractions = {}
            def pre_extraction_callback(matchobj):
                token = os.urandom(16).encode('hex')
                extractions[token] = matchobj.group(0)
                return "{nl2br-%s}" % token
            text = self.pre_extraction_re.sub(pre_extraction_callback, text)

            # in very clear cases, let newlines become <br /> tags
            def newline_callback(matchobj):
                if len(matchobj.group(1)) == 1:
                    return matchobj.group(0).rstrip() + '  \n'
                else:
                    return matchobj.group(0)
            text = self.newline_re.sub(newline_callback, text)

            # Insert pre block extractions
            def pre_insert_callback(matchobj):
                return extractions[matchobj.group(1)]
            text = self.pre_insert_re.sub(pre_insert_callback, text)

            return text.splitlines()
    
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('nl2br', self.Preprocessor(md), '<html_block')




class MathJaxExtension(_markdown.Extension):
    
    class Preprocessor(_markdown.preprocessors.Preprocessor):
         
        _pattern = re.compile(r'\\\[(.+?)\\\]|\\\((.+?)\\\)', re.MULTILINE | re.DOTALL)

        def _callback(self, m):
            return self.markdown.htmlStash.store(cgi.escape(m.group(0)), safe=True)
        
        def run(self, lines):
            """Parses the actual page"""
            return self._pattern.sub(self._callback, '\n'.join(lines)).splitlines()
        
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('mathjax', self.Preprocessor(md), '<html_block')



class MarkdownEscapeExtension(_markdown.Extension):
    
    class Preprocessor(_markdown.preprocessors.Preprocessor):
         
        _pattern = re.compile(r'<nomarkdown>(.+?)</nomarkdown>', re.MULTILINE | re.DOTALL)

        def _callback(self, m):
            return self.markdown.htmlStash.store(m.group(1), safe=True)
        
        def run(self, lines):
            """Parses the actual page"""
            return self._pattern.sub(self._callback, '\n'.join(lines)).splitlines()
        
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('markdown_escape', self.Preprocessor(md), '<html_block')
        

extension_constructors = dict(
    nl2br=Nl2BrExtension,
    mathjax=MathJaxExtension,
    markdown_escape=MarkdownEscapeExtension,
    codehilite=lambda: CodeHiliteExtension([('guess_lang', False)])
)


extension_usage_defaults = dict(
    nl2br=True,
    codehilite=True,
    mathjax=True,
    markdown_escape=False,
)


def markdown(text, **custom_exts):
    
    loaded_extensions = []
    ext_prefs = extension_usage_defaults.copy()
    ext_prefs.update(custom_exts)
    for name, include in ext_prefs.iteritems():
        if include:
            ext = extension_constructors.get(name)
            ext = ext() if ext else name
            loaded_extensions.append(ext)
        
    md = Markdown(extensions=loaded_extensions,
                  safe_mode=False, 
                  output_format='xhtml')
    return md.convert(text)
    

