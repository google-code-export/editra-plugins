# -*- coding: utf-8 -*-
# Name: AbstractSyntaxChecker.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################

""" Abstract syntax checker module """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import threading

#-----------------------------------------------------------------------------#

class SyntaxCheckThread(threading.Thread):
    """Background thread to run checker task in"""
    def __init__(self, checker, target):
        """@param checker: SyntaxChecker object instance
        @param target: callable(data) To receive output data
        """
        super(SyntaxCheckThread, self).__init__()

        # Attributes
        self.checker = checker
        self.target = target

    def run(self):
        data = self.checker.DoCheck()
        wx.CallAfter(self.target, data)

#-----------------------------------------------------------------------------#

class AbstractSyntaxChecker(object):
    def __init__(self, variabledict, filename):
        """ Process dictionary of variables that might be 
        useful to syntax checker.
        """
        super(AbstractSyntaxChecker, self).__init__()

        # Attributes
        self.filename = filename
        self.variabledict = variabledict

    def DoCheck(self):
        """Interface method override to perform the syntax check
        and return a list of tuples.
        @return: [ (Type, Error, Line), ]

        """
        raise NotImplementedError

    def Check(self, callback):
        """Asynchronous method to perform syntax check
        @param callback: callable(data) callback to receive data

        """
        worker = SyntaxCheckThread(self, callback)
        worker.start()

    def _getFileName(self):
        return self.filename
    def _setFileName(self, fname):
        self.filename = fname
    FileName = property(_getFileName, _setFileName)
