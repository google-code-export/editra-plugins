# -*- coding: utf-8 -*-
# Setup script to build the PyTools plugin. To build the plugin
# just run 'python setup.py bdist_egg' and an egg will be built and put into
# the dist directory of this folder.
"""
Adds Python syntax checking using Pylint and debugging using Winpdb with results in a Shelf window.

"""
__author__ = "Mike Rans"

import sys
try:
    from setuptools import setup
except ImportError:
    print "You must have setup tools installed in order to build this plugin"
    setup = None

if setup != None:
    setup(
        name='PyTools',
        version='0.1',
        description=__doc__,
        author=__author__,
        author_email="rans@email.com",
        license="wxWindows",
        url="http://editra.org",
        platforms=["Linux", "OS X", "Windows"],
        packages=['PyTools'],
        entry_points='''
        [Editra.plugins]
        PyTools = PyTools:PyTools
        '''
        )
