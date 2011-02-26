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
import wx.lib.mixins.listctrl as mixins

# Editra Libraries
import eclib.elistmix as elistmix

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class BreakPointsList(wx.ListCtrl,
                       mixins.ListCtrlAutoWidthMixin,
                       elistmix.ListRowHighlighter):
    """List control for displaying syntax check results"""
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        mixins.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

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
        idx = evt.GetIndex()
        fname = self.GetItem(idx, 0).GetText()
        editor = PyToolsUtils.GetEditorForFile(self._mainw, fname)
        nb = self._mainw.GetNotebook()
        if editor:
            nb.ChangePage(editor.GetTabIndex())
        else:
            nb.OnDrop([fname])
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
        filenameText = _("File")
        exprText = _("Expression")
        minLType = max(self.GetTextExtent(filenameText)[0], self.GetColumnWidth(0))
        minLText = max(self.GetTextExtent(exprText)[0], self.GetColumnWidth(2))
        self.errorlines = {}
        self._data = {}
        idx = 0
        for filepath in data:
            linenos = data[filepath]
            for lineno in linenos:
                enabled, exprstr, bpid = linenos[lineno]
                if filename == curpath:
                    editor.SetBreakpoint(int(lineno))
                self._data[idx] = (unicode(filename), unicode(lineno), unicode(exprstr))
                minLType = max(minLType, self.GetTextExtent(filename)[0])
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
