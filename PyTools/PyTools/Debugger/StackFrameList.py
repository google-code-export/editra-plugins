# -*- coding: utf-8 -*-
# Name: StackFrameList.py
# Purpose: Debugger plugin
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
import os.path
import wx

# Editra Libraries
import util
import eclib

# Local Imports
from PyTools.Debugger.RpdbDebugger import RpdbDebugger
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class StackFrameList(eclib.EBaseListCtrl):
    """List control for displaying stack frame results"""
    COL_FRAME = 0
    COL_FILE = 1
    COL_LINE = 2
    COL_FUNCT = 3
    def __init__(self, parent):
        super(StackFrameList, self).__init__(parent)

        # Setup
        self.InsertColumn(StackFrameList.COL_FRAME, _("Frame"))
        self.InsertColumn(StackFrameList.COL_FILE, _("File"))
        self.InsertColumn(StackFrameList.COL_LINE, _("Line"))
        self.InsertColumn(StackFrameList.COL_FUNCT, _("Function"))

        # Attributes
        self.previndex = None

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnFrameSelected)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def select_frame(self, index):
        """Select a frame in the ListCtrl"""
        if (index < 0) or (index > self.GetItemCount() or self.IsSelected(index)):
            return
        self.Select(index)

    def OnFrameSelected(self, evt):
        index = evt.GetIndex()
        if self.previndex == index:
            return
        self.previndex = index
        RpdbDebugger().set_frameindex(index)

        fileName = self.GetItem(index, StackFrameList.COL_FILE).GetText()
        if not fileName:
            return
        editor = PyToolsUtils.GetEditorOrOpenFile(self._mainw, fileName)
        if editor:
            try:
                lineno = int(self.GetItem(index, StackFrameList.COL_LINE).GetText())
                editor.GotoLine(lineno - 1)
            except ValueError:
                util.Log("[PyTools][err] StackFrame: failed to jump to file")

    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()
        self.previndex = None

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of stack info

        """
        fileText = _("File")
        funcText = _("Function")
        minLFile = max(self.GetTextExtent(fileText)[0], self.GetColumnWidth(1))
        minLFunc = max(self.GetTextExtent(funcText)[0], self.GetColumnWidth(3))

        idx = 0
        while idx < len(data):
            frameinfo = data[-(1 + idx)]

            filename = os.path.normcase(frameinfo[0])
            lineno = frameinfo[1]
            function = frameinfo[2]

            efilename = unicode(filename)
            efunction = unicode(function)
            minLFile = max(minLFile, self.GetTextExtent(efilename)[0])
            minLFunc = max(minLFunc, self.GetTextExtent(efunction)[0])
            self.Append((unicode(idx), efilename, unicode(lineno), efunction))
            idx += 1

        self.SetColumnWidth(StackFrameList.COL_FILE, minLFile)
        self.SetColumnWidth(StackFrameList.COL_FUNCT, minLFunc)
        self.previndex = None
        self.Select(0)
