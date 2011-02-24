# -*- coding: utf-8 -*-
# Name: AsyncProcessCreator.py
# Purpose: Create asynchronous processes
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Utility functions """

__author__ = "Mike Rans"
__svnid__ = "$Id: AsyncProcessCreator.py 1025 2010-12-24 18:30:23Z rans@email.com $"
__revision__ = "$Revision: 1025 $"

#-----------------------------------------------------------------------------#
# Imports
from subprocess import STDOUT

# Local Imports
from PyTools.Common.ProcessCreator import ProcessCreator

# Editra Imports
import eclib
#-----------------------------------------------------------------------------#

class AsyncProcessCreator(eclib.ProcessThreadBase, ProcessCreator):
    def __init__(self, parent, info, parentPath, cmdline, pythonpath=None):
        eclib.ProcessThreadBase.__init__(self, parent)
        ProcessCreator.__init__(self, info, parentPath, cmdline, pythonpath)

    def DoPopen(self):
        return self.createprocess(STDOUT)