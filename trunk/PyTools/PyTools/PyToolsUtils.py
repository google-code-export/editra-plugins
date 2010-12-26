# -*- coding: utf-8 -*-
# Name: PyToolsUtils.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Utility functions """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id: PyToolsUtils.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#

import os.path

def get_packageroot(filepath):
    # traverse downwards until we are out of a python package
    fullPath = os.path.abspath(filepath)
    parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

    while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
        childPath = os.path.join(os.path.basename(parentPath), childPath)
        parentPath = os.path.dirname(parentPath)
    return (childPath, parentPath)

def get_modulepath(childPath):
    return os.path.splitext(childPath)[0].replace(os.path.sep, ".")