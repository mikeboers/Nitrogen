"""Script for running all of the tests in the nitrogen package.

Imports ALL of the modules (except those in lib), looks for unittest stuff
in them, and looks for doctests.

Runs all of the files that are of the form *.test as doctests.

"""


import os
import sys
import unittest
import doctest

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
            if '/lib' in path or path == __file__:
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
            suite = doctest.DocFileSuite(path, module_relative=False)
            suites.append(suite)

runner = unittest.TextTestRunner()
suite = unittest.TestSuite()
suite.addTests(suites)
runner.run(suite)
