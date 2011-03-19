# -*- coding: utf-8 -*-
# Name: FindResultsList.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

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

class FindResultsList(eclib.EBaseListCtrl):
    """List control for displaying breakpoints results"""
    def __init__(self, parent):
        super(FindResultsList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("File"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def OnItemActivate(self, evt):
        """Go to the file"""
        idx = evt.GetIndex()
        fname = self.GetItem(idx, 0).GetText()
        if fname.find("INFO:") != -1:
            return
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mainw, fname)

    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: list(file)

        """
        self._data = {}
        for idx, eText in enumerate(data):
            eText = unicode(eText).rstrip()
            self._data[idx] = (eText,)
            self.Append(self._data[idx])
            self.SetItemData(idx, idx)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
