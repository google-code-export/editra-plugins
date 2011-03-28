# -*- coding: utf-8 -*-
# Name: AbstractModuleFinder.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################

""" Abstract Module Finder module """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
from PyTools.Common.PyToolsUtils import RunProcInThread

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

    def RunModuleFind(self):
        """Interface method override to perform the module find
        and return a list of tuples.
        @return: [ (Filepath), ]

        """
        raise NotImplementedError

    def Find(self, callback):
        """Asynchronous method to perform module find
        @param callback: callable(data) callback to receive data

        """
        worker = RunProcInThread("Find", callback, self.RunModuleFind)
        worker.start()

    #---- Properties ----#
    ModuleToFind = property(lambda self: self.moduletofind,
                            lambda self, name: setattr(self, 'moduletofind', name))
