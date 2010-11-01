# -*- coding: utf-8 -*-
# Name: AbstractSyntaxChecker.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################

""" Abstract syntax checker module """

__version__ = "0.2"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#

class AbstractSyntaxChecker(object):
    def __init__(self, variabledict, filename):
        """ Process dictionary of variables that might be useful to syntax checker
        """
        self.filename = filename
        self.variabledict = variabledict
        
    def Check(self):
        """ Return a list of
            [ (Type, error, line), ... ]
            Type is 'Error' or 'Warning'
        """
        pass
