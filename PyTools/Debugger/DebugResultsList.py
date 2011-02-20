# -*- coding: utf-8 -*-
# Name: DebugResultsList.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: DebugResultsList.py -1   $"
__revision__ = "$Revision: -1 $"

#----------------------------------------------------------------------------#
# Imports
import wx
import wx.lib.mixins.listctrl as mixins

# Editra Imports
import ed_msg
import eclib.elistmix as elistmix
import util

# Local Imports
from Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class DebugResultsList(wx.ListCtrl,
                       mixins.ListCtrlAutoWidthMixin,
                       elistmix.ListRowHighlighter):
    """List control for displaying syntax check results"""
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        mixins.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

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
        editor = PyToolsUtils.GetEditorForFile(self._mainw, fname)
        nb = self._mainw.GetNotebook()
        if editor:
            nb.ChangePage(editor.GetTabIndex())
        else:
            nb.OnDrop([fname])

    def DeleteOldRows(self):
        """Delete all the rows """
        for itemIndex in reversed(xrange(0, self.GetItemCount())):
            self.DeleteItem(itemIndex)

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: list(file)

        """
        self._data = {}
        idx = 0
        for eText in data:
            eText = unicode(eText).rstrip()
            self._data[idx] = (eText,)
            self.Append(self._data[idx])
            self.SetItemData(idx, idx)
            idx += 1

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
