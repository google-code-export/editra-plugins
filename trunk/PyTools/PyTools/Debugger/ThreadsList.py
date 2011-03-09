# -*- coding: utf-8 -*-
# Name: ThreadsList.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: ThreadsList.py -1   $"
__revision__ = "$Revision: -1 $"

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
        self.suppress_recursion = 0
        
        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnThreadSelected)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def check_suppress_recursion(self):
        if self.suppress_recursion > 0:
            self.suppress_recursion -= 1
            return True
        return False

    def update_thread(self, thread_id, thread_name, fBroken):
        index = self.FindItemData(-1, thread_id)
        if index < 0:
            return -1

        self.SetStringItem(index, 1, thread_name)
        self.SetStringItem(index, 2, [rpdb2.STATE_RUNNING, rpdb2.STR_STATE_BROKEN][fBroken])

        return index
        
    def OnThreadSelected(self, evt):
        """Go to the file"""
        if self.suppress_recursion == 0:
            self.suppress_recursion += 1
            tid = self.GetItemData(index)
            RPDBDEBUGGER.set_thread(tid)
        else:
            self.suppress_recursion -= 1

        event.Skip()
        
    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()

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
            estate = unicode(["running", "waiting at break point"][fBroken])
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
            self.suppress_recursion += 1
            self.Select(selectedidx)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
