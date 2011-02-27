# -*- coding: utf-8 -*-
# Name: ShelfWindowManager.py
# Purpose: Manages shelf windows
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf Manager"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
class ShelfWindowManager(object):
    def __init__(self):
        super(ShelfWindowManager, self).__init__()
        self.lintshelfwindow = None
        self.findshelfwindow = None
        self.debugshelfwindow = None
        self.breakpointsshelfwindow = None
        self.stackframeshelfwindow = None

    def __FindMainWindow(self):
        """Find the mainwindow of this control
        @return: MainWindow or None
        """
        def IsMainWin(win):
            """Check if the given window is a main window"""
            return getattr(tlw, '__name__', '') == 'MainWindow'

        tlw = self.GetTopLevelParent()
        if IsMainWin(tlw):
            return tlw
        elif hasattr(tlw, 'GetParent'):
            tlw = tlw.GetParent()
            if IsMainWin(tlw):
                return tlw

        return None
        
    def setLintShelfWindow(self, lintshelfwindow):
        self.lintshelfwindow = lintshelfwindow
        
    def getLintShelfWindow(self):
        return self.lintshelfwindow
        
    def setFindShelfWindow(self, findshelfwindow):
        self.findshelfwindow = findshelfwindow
        
    def getFindShelfWindow(self):
        return self.findshelfwindow
        
    def setDebugShelfWindow(self, debugshelfwindow):
        self.debugshelfwindow = debugshelfwindow
        
    def getDebugShelfWindow(self):
        return self.debugshelfwindow
        
    def setBreakpointsShelfWindow(self, breakpointsshelfwindow):
        self.breakpointsshelfwindow = breakpointsshelfwindow
        
    def getBreakpointsShelfWindow(self):
        return self.breakpointsshelfwindow
        
    def setStackFrameShelfWindow(self, stackframeshelfwindow):
        self.stackframeshelfwindow = stackframeshelfwindow
        
    def getStackFrameShelfWindow(self):
        return self.stackframeshelfwindow
                