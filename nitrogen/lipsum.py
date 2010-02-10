
from __future__ import absolute_import

from lipsum import Generator

g = Generator

def sentence(start_with_lorem=False):
    return g.generate_sentence(start_with_lorem)

def paragraph(start_with_lorem=False):
    return g.generate_paragraph(start_with_lorem)