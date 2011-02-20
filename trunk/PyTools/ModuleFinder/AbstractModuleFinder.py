# -*- coding: utf-8 -*-
# Name: AbstractModuleFinder.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################

""" Abstract Module Finder module """

__author__ = "Mike Rans"
__svnid__ = "$Id: AbstractModuleFinder.py 1071 2011-02-17 20:49:32Z rans@email.com $"
__revision__ = "$Revision: 1071 $"

#-----------------------------------------------------------------------------#
# Imports
from Common.PyToolsUtils import RunProcInThread

#-----------------------------------------------------------------------------#

class AbstractModuleFinder(object):
    def __init__(self, variabledict, moduletofind):
        """ Process dictionary of variables that might be
        useful to module finder.
        """
        super(AbstractModuleFinder, self).__init__()

        # Attributes
        self.moduletofind = moduletofind
        self.variabledict = variabledict

    def DoFind(self):
        """Interface method override to perform the module find
        and return a list of tuples.
        @return: [ (Filepath), ]

        """
        raise NotImplementedError

    def Find(self, callback):
        """Asynchronous method to perform module find
        @param callback: callable(data) callback to receive data

        """
        worker = RunProcInThread(self.DoFind, callback, "Find")
        worker.start()

    def _getModule(self):
        return self.moduletofind
    def _setModule(self, moduletofind):
        self.moduletofind = moduletofind
    ModuleToFind = property(_getModule, _setModule)
