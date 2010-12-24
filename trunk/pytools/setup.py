# -*- coding: utf-8 -*-
# Setup script to build the pytools plugin. To build the plugin
# just run 'python setup.py bdist_egg' and an egg will be built and put into
# the dist directory of this folder.
"""Adds various Python tools with results shown in a Shelf window.

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
        name='pytools',
        version='0.1',
        description=__doc__,
        author=__author__,
        author_email="rans@email.com",
        license="wxWindows",
        url="http://editra.org",
        platforms=["Linux", "OS X", "Windows"],
        packages=['pytools'],
        entry_points='''
        [Editra.plugins]
        pytools = pytools:pytools
        '''
        )
