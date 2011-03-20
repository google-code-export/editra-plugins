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
import eclib

# Local Imports
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class StackFrameList(eclib.EBaseListCtrl):
    """List control for displaying stack frame results"""
    def __init__(self, parent):
        super(StackFrameList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("Frame"))
        self.InsertColumn(1, _("File"))
        self.InsertColumn(2, _("Line"))
        self.InsertColumn(3, _("Function"))

        # Attributes
        self.previndex = None
        
        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnFrameSelected)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def select_frame(self, index):
        if (index < 0) or (index > self.GetItemCount()):
            return

        if self.IsSelected(index):
            return
            
        self.Select(index)

    def OnFrameSelected(self, evt):
        index = evt.m_itemIndex
        if self.previndex == index:
            return
        self.previndex = index
        RPDBDEBUGGER.set_frameindex(index)

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
        
        self._data = {}
        idx = 0
        while idx < len(data):
            frameinfo = data[-(1 + idx)]
            
            filename = os.path.normcase(frameinfo[0])
            lineno = frameinfo[1]
            function = frameinfo[2]

            efilename = unicode(filename)
            efunction = unicode(function)
            self._data[idx] = (unicode(idx), efilename, unicode(lineno), efunction)
            minLFile = max(minLFile, self.GetTextExtent(efilename)[0])
            minLFunc = max(minLFunc, self.GetTextExtent(efunction)[0])
            self.Append(self._data[idx])
            self.SetItemData(idx, idx)

            idx += 1
            
        self.SetColumnWidth(1, minLFile)
        self.SetColumnWidth(3, minLFunc)
        self.previndex = None
        self.Select(0)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""