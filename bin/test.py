"""Script for running all of the tests in the nitrogen package.

Imports ALL of the modules (except those in lib), looks for unittest stuff
in them, and looks for doctests.

Runs all of the .test files in the test directory as doc tests.

"""


import os
import sys

root_path = os.path.abspath(__file__ + '/../../..')
sys.path.append(root_path)

modules = []
docfiles = []

for dirpath, dirnames, filenames in os.walk(root_path + '/nitrogen'):
    for name in filenames:
        if name.endswith('.py'):
            modules.append(dirpath + '/' + name)
        elif name.endswith('.text.txt'):
            docfiles.append(dirpath + '/' + name)

print '\n'.join(modules)