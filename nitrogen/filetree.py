import os

def Node(path):
    return DirNode(path) if os.path.isdir(path) else FileNode(path)

class FileNode(object):
    
    _indent_base = '+   '
    
    def __init__(self, path):
        self.path = path
        self.type = 'file'
        self.size = os.path.getsize(path)
        self.mtime = int(os.path.getmtime(path))
    
    @property
    def name(self):
        return os.path.split(self.path)[1]
    
    @property
    def dirname(self):
        return os.path.split(self.path)[0]
    
    @property
    def base(self):
        return os.path.splitext(self.name)[0]

    @property
    def ext(self):
        return os.path.splitext(self.path)[1] 
    
    @property
    def is_dir(self):
        return self.type == 'dir'
    
    @property
    def is_file(self):
        return self.type == 'file'
           
    def __repr__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.path)
    
    def tree_string(self, indent = 0, absolute = False):
        return self._indent_base * indent + (self.path if absolute else '/' + self.name)
        
    def flat_iter(self):
        yield self
    
    def dict(self):
        return {
            'name': self.name,
            'type': self.type,
            'size': self.size,
            'mtime': self.mtime
        }
    
class DirNode(FileNode):
    
    def __init__(self, path):
        super(DirNode, self).__init__(path)
        self.type = 'dir'
        self.children = {}
    
    def child_names(self):
        return sorted(self.children.keys(), key=lambda k: k.lower())
    
    def tree_string(self, indent = 0, absolute = False):
        string = super(DirNode, self).tree_string(indent, absolute)
        for name in self.child_names():
            string += '\n' + self.children[name].tree_string(indent + 1, False)
        return string
    
    def flat_path_iter(self, absolute = False):
        base = (self.path if absolute else self.name)
        for name in self.child_names():
            yield base + '/' + name
            for sub_name in self.children[name].flat_path_iter():
                yield base + '/' + sub_name
    
    def flat_iter(self):
        yield self
        for name in self.child_names():
            for i in self.children[name].flat_iter():
                yield i
    
    def dict(self):
        d = super(DirNode, self).dict()
        d['children'] = []
        for name in sorted(self.children.keys(), key=lambda k: k.lower()):
            d['children'].append(self.children[name].dict())
        return d

class RootNode(DirNode):
    
    def dict(self):
        d = super(RootNode, self).dict()
        d['root'] = self.path
        return d
    
    @staticmethod
    def _name_filter(l):
        for v in l:
            if v.startswith('.'):
                l.remove(v)
    
    def __init__(self, path, depth=None):
        super(RootNode, self).__init__(path)
        # iterate across the tree
        for dirname, dirs, files in walker(path, max_depth=depth):
            # chop the root path off the front
            dirname = dirname[len(path):]
            dirname = dirname.split('/')[1:]
            # descend into the tree to find the node that this is secribing
            node = self
            for name in dirname:
                node = node.children[name]
            # strip out directories and files that start with '.'
            self._name_filter(dirs)
            self._name_filter(files)
            # create child nodes for all of these
            for name in dirs:
                node.children[name] = DirNode('%s/%s' % (node.path, name))
            for name in files:
                node.children[name] = FileNode('%s/%s' % (node.path, name))

def walker(dirname, max_depth=None, depth=0):
    dirs = []
    files = []
    for name in os.listdir(dirname):
        if os.path.isdir('%s/%s' % (dirname, name)):
            dirs.append(name)
        else:
            files.append(name)
    yield dirname, dirs, files
    if depth < max_depth:
        for name in dirs:
            for x in walker('%s/%s' % (dirname, name), max_depth, depth + 1):
                yield x

if __name__ == '__main__':  
    import time
    import json  
       
    start_time = time.time()
    
    root_path = '/Server/www/pixray.ca'
    

        
    
    # for d, ds, fs in walker(root_path, 1):
    #     for i, name in enumerate(ds[:]):
    #         if name.startswith('.'):
    #             del ds[i]
    #     print d
    #     print '\t/' + '\n\t/'.join(ds)
    #     print '\t' + '\n\t'.join(fs)
    
    root = RootNode(root_path, 0)
    # print root.tree_string()
    # for n in root.flat_iter():
    #     print n
    
    print json.dumps(root.dict(), indent=4)
    print time.time() - start_time