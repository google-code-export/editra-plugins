# -*- coding: utf-8 -*-
# Name: ThreadsList.py
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
import wx

# Editra Libraries
import eclib

# Local Imports
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation
#----------------------------------------------------------------------------#

class ThreadsList(eclib.EBaseListCtrl):
    """List control for displaying thread thread results"""
    def __init__(self, parent):
        super(ThreadsList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("Thread Id"))
        self.InsertColumn(1, _("Name"))
        self.InsertColumn(2, _("State"))
        
        # Attributes
        self.previndex = None
        
        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnThreadSelected)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def update_thread(self, thread_id, thread_name, fBroken):
        index = self.FindItemData(-1, thread_id)
        if index < 0:
            return

        self.SetStringItem(index, 1, thread_name)
        self.SetStringItem(index, 2, [u"running", u"waiting at breakpoint"][fBroken])
        
    def OnThreadSelected(self, evt):
        index = evt.m_itemIndex
        if self.previndex == index:
            return
        self.previndex = index
        tid = self.GetItemData(index)
        RPDBDEBUGGER.set_thread(tid)
        
    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()
        self.previndex = None

    def PopulateRows(self, current_thread, threads_list):
        """Populate the list with the data
        @param current_thread: current threads
        @param threads_list: list of threads

        """
        nameText = _("Name")
        stateText = _("State")
        minLName = max(self.GetTextExtent(nameText)[0], self.GetColumnWidth(1))
        minLState = max(self.GetTextExtent(stateText)[0], self.GetColumnWidth(2))
        
        self._data = {}
        selectedidx = None
        for idx, threadinfo in enumerate(threads_list):
            tid = threadinfo["tid"]
            name = threadinfo["name"]
            fBroken = threadinfo["broken"]

            ename = unicode(name)
            estate = [u"running", u"waiting at breakpoint"][fBroken]
            self._data[idx] = (unicode(tid), ename, estate)
            minLName = max(minLName, self.GetTextExtent(ename)[0])
            minLState = max(minLState, self.GetTextExtent(estate)[0])
            self.Append(self._data[idx])
            self.SetItemData(idx, tid)
            if tid == current_thread:
                selectedidx = idx
            
        self.SetColumnWidth(1, minLName)
        self.SetColumnWidth(2, minLState)
        if selectedidx is not None:
            self.previndex = None
            self.Select(selectedidx)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
