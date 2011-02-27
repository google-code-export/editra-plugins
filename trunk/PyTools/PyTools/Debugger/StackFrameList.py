# -*- coding: utf-8 -*-
# Name: StackFrameList.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: StackFrameList.py -1   $"
__revision__ = "$Revision: -1 $"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class StackFrameList(eclib.EBaseListCtrl):
    """List control for displaying stack frame results"""
    def __init__(self, parent):
        super(StackFrameList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("File"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Expression"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def OnItemActivate(self, evt):
        """Go to the file"""
        pass

    def Clear(self):
        """Delete all the rows """
        for itemIndex in reversed(xrange(0, self.GetItemCount())):
            self.DeleteItem(itemIndex)

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of breakpoints

        """
        pass
        
    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
