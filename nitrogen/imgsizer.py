
from __future__ import division

import math
import os
import logging
import Image as image
from cStringIO import StringIO
import datetime
import hashlib
import sys

from .uri.query import Query
from .http.status import HttpNotFound
from .request import as_request


log = logging.getLogger(__name__)

# TODO:
# - take max_age from config


MODE_FIT = 'fit'
MODE_CROP = 'crop'
MODE_PAD = 'pad'
MODES = (MODE_FIT, MODE_CROP, MODE_PAD)




class Request(dict):
    
    ARGS = [
        ('mode', 'm'),
        ('width', 'w'),
        ('height', 'h'),
        ('background', 'bg'),
        ('quality', 'q'),
        ('format', 'f'),
    ]
    LONG_TO_SHORT = dict(ARGS)
    SHORT_TO_LONG = dict(list(reversed(x)) for x in ARGS)
    
    def __init__(self, path, *args, **kwargs):
        
        self.path = path
        
        raw = dict(*args, **kwargs)
        
        for k, v in raw.items():
            k = self.SHORT_TO_LONG.get(k, k)
            if k not in self.LONG_TO_SHORT:
                continue
            self[k] = v
        
        # Dimensions should be ints.
        for k in 'width', 'height':
            self[k] = int(self[k]) if k in self else None
        
        # Quality should always be an int, and default to 75.
        self['quality'] = int(self.get('quality', 75))
        
        # Figure out a format default.
        format = self.get('format') or os.path.splitext(path)[1][1:].lower()
        format = {'jpg' : 'jpeg'}.get(format, format) or 'jpeg'
        self['format'] = format.lower()
    
    def short_items(self):
        return [(self.LONG_TO_SHORT[k], v) for k, v in self.items()]
    
    def __getattr__(self, name):
        return self.get(name)
    
    def __getitem__(self, name):
        return self.get(name)
    
    def __iter__(self):
        for k, v in self.ARGS:
            if v is not None:
                yield k
    
    @property
    def cache_key(self):
        return hashlib.md5(repr((self.path, ) + tuple(self.get(k) for k in self.ARGS))).hexdigest()
    
    @property
    def width(self):
        try:
            return int(self['width'])
        except:
            return None
    
    @property
    def height(self):
        try:
            return int(self['height'])
        except:
            return None
    
    @property
    def quality(self):
        try:
            return int(self['quality'])
        except:
            return 85


class ImgSizer(object):
    
    
    def __init__(self, path, cache_root=None, sig_key=None, max_age=3600):
        self.path = [os.path.abspath(x) for x in path]
        self.cache_root = cache_root
        self.sig_key = sig_key
        self.max_age = max_age
    
    def build_url(self, local_path, **kwargs):
        query = Query(Request(local_path, kwargs).short_items())
        if self.sig_key:
            query['path'] = local_path
            query.sign(self.sig_key, add_time=False, add_nonce=False)
            del query['path']
        return local_path + ('?' + str(query) if kwargs else '')
        
    def find_img(self, local_path):
        local_path = local_path.lstrip('/')
        for path_base in self.path:
            path = os.path.join(path_base, local_path)
            if os.path.exists(path):
                return path
    
    def resize(self, img, width=None, height=None, mode=None, background=None):
        
        orig_width, orig_height = img.size

        width = min(width, orig_width) if width else None
        height = min(height, orig_height) if height else None
        
        if not img.mode.lower().startswith('rgb'):
            img = img.convert('RGBA')
        
        if width and height:
    
            fit, crop = sorted([
                (width, orig_height * width // orig_width),
                (orig_width * height // orig_height, height)
            ])
    
            if mode == 'fit' or mode == 'pad':
                img = img.resize(fit, image.ANTIALIAS)
                
                if mode == 'pad':
                    pad_color = {'white': (255, 255, 255)}.get(str(background).lower(), 0)
                    back = image.new('RGBA', (width, height), pad_color)
                    back.paste(img, (
                        (width  - fit[0]) // 2,
                        (height - fit[1]) // 2
                    ))
                    img = back
            
            elif mode == 'crop':
                dx = (crop[0] - width) // 2
                dy = (crop[1] - height) // 2
                img = img.resize(crop, image.ANTIALIAS).crop(
                    (dx, dy, dx + width, dy + height)
                )
            
            else:
                img = img.resize((width, height), image.ANTIALIAS)
        
        elif width:
            height = orig_height * width // orig_width
            img = img.resize((width, height), image.ANTIALIAS)

        elif height:
            width = orig_width * height // orig_height
            img = img.resize((width, height), image.ANTIALIAS)
        
        return img
    
    @as_request
    def __call__(self, req, res):
        
        # log.debug(req.unrouted)
        # log.debug(repr(self.path))
        
        path = self.find_img(req.unrouted)
        if not path:
            raise HttpNotFound()
        
        if self.sig_key:
            query = Query(req.get)
            query['path'] = req.unrouted
            if not query.verify(self.sig_key):
                log.warning('signature not accepted')
                raise HttpNotFound()
        
        if self.max_age:
            res.max_age = self.max_age
        
        raw_mtime = os.path.getmtime(path)
        mtime = datetime.datetime.utcfromtimestamp(raw_mtime)
        res.last_modified = mtime
        if req.if_modified_since and req.if_modified_since >= mtime:
            res.start('not modified')
            return
        
        img_req    = Request(path, req.get)
        
        mode       = img_req.mode
        background = img_req.background
        width      = img_req.width
        height     = img_req.height
        quality    = img_req.quality
        format     = img_req.format

        out = None
        cache_path = None
        
        if self.cache_root:
            cache_path = os.path.join(self.cache_root, img_req.cache_key + '.' + format)
            cache_mtime = os.path.getmtime(cache_path) if os.path.exists(cache_path) else None
            if cache_mtime is not None and cache_mtime >= raw_mtime:
                # We have it cached here!
                out = open(cache_path, 'rb').read()
        
        if not out:
            
            img = image.open(path)
            img = self.resize(img, width=width, height=height, mode=mode, background=background)
    
            out_file = StringIO()
            img.save(out_file, format, quality=quality)
            out = out_file.getvalue()
            
            if cache_path:
                try:
                    cache_file = open(cache_path, 'wb')
                    cache_file.write(out)
                    cache_file.close()
                except Exception as e:
                    log.exception('error while saving image to cache')
    
        etag = hashlib.md5(out).hexdigest()
        res.etag = etag
        if req.etag and req.etag == etag:
            res.start('not modified')
            return
    
        res.headers['content-type'] = 'image/%s' % format
        res.start()
        yield out



if __name__ == '__main__':
    #
    __app__ = ImgSizer(
        path=[],
        sig_key='awesome'
    )
    print __app__.build_url('/mock/photos/2459172663_35af8640ff.jpg', width=200)