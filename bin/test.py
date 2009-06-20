# encoding: utf8
"""Script for running all of the tests in the nitrogen package.

Imports ALL of the modules (except those in lib), looks for unittest stuff
in them, and looks for doctests.

Runs all of the files that are of the form *.test as doctests.

"""


import os
import sys
import unittest
import doctest

# class utf8_out(object):
#     def __init__(self, out):
#         self.out = out
#     def write(self, stuff):
#         if isinstance(stuff, unicode):
#             stuff = stuff.encode('utf8')
#         return self.out.write(stuff)
#         
# sys.stdout = utf8_out(sys.stdout)
# sys.stderr = utf8_out(sys.stderr)

# Add the path ABOVE nirogen to the path
root_path = os.path.abspath(__file__ + '/../../..')
sys.path.append(root_path)

suites = []

# Searching for paths...
for dirpath, dirnames, filenames in os.walk(root_path + '/nitrogen'):
    for name in filenames:
        if name.endswith('.py'):
            path = dirpath + '/' + name
            
            # Skip the library.
            if '/lib/' in path or '/bin/' in path:
                continue
            
            # Turn it into a module
            name = path[len(root_path) + 1:-3].replace('/', '.')
            try:
                m = __import__(name, fromlist=['force'])
                suite = unittest.defaultTestLoader.loadTestsFromModule(m)
                suites.append(suite)
                try:
                    suite = doctest.DocTestSuite(m)
                    suites.append(suite)
                except ValueError as e:
                    if e.args[1] != 'has no tests':
                        raise
            except Exception as e:
                print 'Could not import module %s:' % name
                print '\t%r' % e
            
        elif name.endswith('.test'):
            path = dirpath + '/' + name
            suite = doctest.DocFileSuite(path, module_relative=False, encoding='UTF-8')
            suites.append(suite)

runner = unittest.TextTestRunner()
suite = unittest.TestSuite()
suite.addTests(suites)
runner.run(suite)
