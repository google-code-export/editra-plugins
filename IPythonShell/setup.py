# -*- coding: utf-8 -*-
# Setup script to build the IPythonShell plugin. To build the plugin
# just run 'python setup.py bdist_egg' and an egg will be built and put into 
# the dist directory of this folder.
"""Adds an interactive IPythonShell that can be opened in the Shelf. Multiple
instances can be opened in the Shelf at once.
"""
__author__ = "Laurent Dufrechou"

import sys
try:
    from setuptools import setup
except ImportError:
    print "You must have setup tools installed in order to build this plugin"
    setup = None

if setup != None:
    setup(
        name='IPyShell',
        version='0.1',
        description=__doc__,
        author=__author__,
        author_email="laurent.dufrechou@gmail.com",
        license="bsd",
        url="http://ipython.scipy.org/moin/About",
        platforms=["Linux", "OS X", "Windows"],
        packages=['IPyShell'],
        entry_points='''
        [Editra.plugins]
        IPyShell = IPyShell:IPyShell
        '''
        )
