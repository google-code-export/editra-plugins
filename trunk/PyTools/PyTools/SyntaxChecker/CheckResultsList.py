# -*- coding: utf-8 -*-
# Name: CheckResultsList.py
# Purpose: Pylint plugin
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
from wx.stc import STC_INDIC_SQUIGGLE

# Editra Libraries
import ed_msg
import eclib

# Local imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class CheckResultsList(eclib.EBaseListCtrl):
    """List control for displaying syntax check results"""
    def __init__(self, parent):
        super(CheckResultsList, self).__init__(parent)

        # Attributes
        self.editor = None
        self.showedtip = False
        self.errorlines = dict()

        # Setup
        self.InsertColumn(0, _("Type"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Error"))
        self.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)

        # Message Handler
        ed_msg.Subscribe(self.OnDwellStart, ed_msg.EDMSG_UI_STC_DWELL_START)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, evt):
        if evt.GetEventObject() is self:
            ed_msg.Unsubscribe(self.OnDwellStart)

    def set_mainwindow(self, mw):
        self._mainw = mw

    def set_editor(self, editor):
        self.editor = editor

    def OnDwellStart(self, msg):
        """Show calltips for the error if dwelling over a line"""
        data = msg.GetData()
        buf = data.get('stc', None)
        if buf and buf == self.editor:
            lineno = data.get('line', -1)
            errorlist = self.errorlines.get(lineno)
            if errorlist:
                data['rdata'] = "\n".join(errorlist)

    def OnItemActivate(self, evt):
        """Go to the error in the file"""
        if not self.editor:
            return
        idx = evt.GetIndex()
        itm = self.GetItem(idx, 1).GetText()
        try:
            lineNo = int(itm)
            self.editor.GotoLine(max(0, lineNo - 1))
        except ValueError:
            pass

    def Clear(self):
        """Delete all the rows """
        if not self.editor:
            return
        self.DeleteAllItems()
        PyToolsUtils.unset_indic(self.editor)
        self.errorlines = {}

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: list of tuples (errorType, errorText, errorLine)

        """
        if not self.editor:
            return
        self.editor.IndicatorSetStyle(2, STC_INDIC_SQUIGGLE)
        self.editor.IndicatorSetForeground(2, 'red')

        typeText = _("Type")
        errorText = _("Error")
        minLType = max(self.GetTextExtent(typeText)[0], self.GetColumnWidth(0))
        minLText = max(self.GetTextExtent(errorText)[0], self.GetColumnWidth(2))
        self.errorlines = {}
        self._data = {}
        for idx, (eType, eText, eLine) in enumerate(data):
            eText = unicode(eText).rstrip()
            self._data[idx] = (unicode(eType), unicode(eLine), eText)
            minLType = max(minLType, self.GetTextExtent(eType)[0])
            minLText = max(minLText, self.GetTextExtent(eText)[0])
            self.Append(self._data[idx])
            self.SetItemData(idx, idx)

            try:
                lineNo = int(eLine)
                errorlist = self.errorlines.get(lineNo)
                if not errorlist:
                    errorlist = []
                    self.errorlines[lineNo] = errorlist
                errorlist.append(eText)
                if eType == "Error":
                    PyToolsUtils.set_indic(lineNo - 1, self.editor)
            except ValueError:
                pass
        self.SetColumnWidth(0, minLType)
        self.SetColumnWidth(2, minLText)

    @staticmethod
    def _printListCtrl(ctrl):
        for row in xrange(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
