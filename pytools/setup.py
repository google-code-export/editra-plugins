# -*- coding: utf-8 -*-
# Setup script to build the pytools plugin. To build the plugin
# just run 'python setup.py bdist_egg'

"""Various Python tools for Editra"""


__author__ = "Ofer Schwarz, Rudi Pettazzi, Alexey Zankevich"

import sys
try:
    from setuptools import setup
except ImportError:
    print "You must have setuptools installed in order to build this plugin"
    setup = None

if setup != None:
    setup(name='PyTools',
          version='0.1',
          description=__doc__,
          author=__author__,
          author_email="os.urandom@gmail.com",
          license="wxWindows",
          url="http://editra.org",
          platforms=["Linux", "OS X", "Windows"],
          packages=['pytools', 'pytools.foxtrot'],
          entry_points='''
          [Editra.plugins]
          PyTools = pytools:PyTools
          '''
          )
