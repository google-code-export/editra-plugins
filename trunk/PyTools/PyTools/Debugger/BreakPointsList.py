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
import os.path

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class BreakPointsList(eclib.EToggleEditListCtrl):
    """List control for displaying breakpoints results"""
    def __init__(self, parent):
        super(BreakPointsList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("File"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Expression"))

        # Attributes
        self.parent = parent
        
        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnItemRightClicked)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnItemEdited)
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def OnItemRightClicked(self, evt):
        """Go to the file"""
        idx = evt.GetIndex()
        fileName = self.GetItem(idx, 0).GetText()
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mainw, fileName)
        lineno = int(self.GetItem(idx, 1).GetText())
        editor.GotoLine(lineno - 1)

    def _seteditorbreakpoint(self, filepath, lineno, enabled, delete=False):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            curpath = os.path.normcase(editor.GetFileName())
            if filepath == curpath:
                editorlineno = lineno - 1
                if delete:
                    editor.DeleteBreakpoint(editorlineno)
                    return
                if enabled:
                    editor.SetBreakpoint(editorlineno)
                else:
                    editor.SetBreakpointDisabled(editorlineno)
    
    def OnItemEdited(self, evt):
        if evt.IsEditCancelled():
            evt.Veto()
            return
        index = evt.GetIndex()
        newval = evt.GetLabel()
        column = evt.GetColumn()
        filepath, linenostr, exprstr = self._data[index]
        lineno = int(linenostr)
        self.parent.DeleteBreakpoint(filepath, lineno)
        self._seteditorbreakpoint(filepath, lineno, False, True)
        if column == 0:
            filepath = newval
        elif column == 1:
            lineno = int(newval)
        else:
            exprstr = newval
        enabled = self.IsChecked(index)
        self.parent.SetBreakpoint(filepath, lineno, exprstr, enabled)
        self._data[index] = (unicode(filepath), unicode(lineno), unicode(exprstr))
        self._seteditorbreakpoint(filepath, lineno, enabled)

    def OnCheckItem(self, index, enabled):
        filepath, linenostr, exprstr = self._data[index]
        lineno = int(linenostr)
        self.parent.ChangeBreakpoint(filepath, lineno, exprstr, enabled)
        self._seteditorbreakpoint(filepath, lineno, enabled)
                    
    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            editor.DeleteAllBreakpoints()

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of breakpoints

        """
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
                self._seteditorbreakpoint(filepath, lineno, enabled)
                self._data[idx] = (unicode(filepath), unicode(lineno), unicode(exprstr))
                minLType = max(minLType, self.GetTextExtent(filepath)[0])
                minLText = max(minLText, self.GetTextExtent(exprstr)[0])
                self.Append(self._data[idx])
                self.SetItemData(idx, idx)
                self.CheckItem(idx, enabled)
                idx += 1
        self.SetColumnWidth(0, minLType)
        self.SetColumnWidth(2, minLText)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
