# -*- coding: utf-8 -*-
# Name: BreakPointsList.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: BreakPointsList.py -1   $"
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

class BreakPointsList(eclib.EEditListCtrl):
    """List control for displaying breakpoints results"""
    def __init__(self, parent):
        super(BreakPointsList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("File"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Expression"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClicked)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def OnItemRightClicked(self, evt):
        """Go to the file"""
        idx = evt.GetIndex()
        fileName = self.GetItem(idx, 0).GetText()
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mainw, fileName)
        lineno = int(self.GetItem(idx, 1).GetText())
        editor.GotoLine(lineno)

    def Clear(self):
        """Delete all the rows """
        for itemIndex in reversed(xrange(0, self.GetItemCount())):
            self.DeleteItem(itemIndex)

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of breakpoints

        """
        curpath = None
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            curpath = editor.GetFileName()
            editor.DeleteAllBreakpoints()
        filenameText = _("File")
        exprText = _("Expression")
        minLType = max(self.GetTextExtent(filenameText)[0], self.GetColumnWidth(0))
        minLText = max(self.GetTextExtent(exprText)[0], self.GetColumnWidth(2))
        self._data = {}
        idx = 0
        for filepath in data:
            linenos = data[filepath]
            for lineno in linenos:
                enabled, exprstr, bpid = linenos[lineno]
                if filepath == curpath:
                    editor.SetBreakpoint(int(lineno) - 1)
                self._data[idx] = (unicode(filepath), unicode(lineno), unicode(exprstr))
                minLType = max(minLType, self.GetTextExtent(filepath)[0])
                minLText = max(minLText, self.GetTextExtent(exprstr)[0])
                self.Append(self._data[idx])
                self.SetItemData(idx, idx)
                idx += 1
        self.SetColumnWidth(0, minLType)
        self.SetColumnWidth(2, minLText)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
