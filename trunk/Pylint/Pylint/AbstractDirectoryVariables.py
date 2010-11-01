# -*- coding: utf-8 -*-
# Name: AbstractDirectoryVariables.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Directory Variables module """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#

class AbstractDirectoryVariables(object):
    def __init__(self, filetype):
        self.dirvarfilename = "__dirvar_%s__.cfg" % filetype
    
    def read_dirvarfile(self, filepath):
        """ Return a dict of variables for usage by tools eg. pylint
        """
        return {}
    
    def close(self):
        """ anything to remove or shut down """
        pass