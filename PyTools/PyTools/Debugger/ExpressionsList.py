# -*- coding: utf-8 -*-
# Name: ExpressionsList.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id: ExpressionsList.py -1   $"
__revision__ = "$Revision: -1 $"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import eclib

# Local Imports
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class ExpressionsList(eclib.EToggleEditListCtrl):
    """List control for displaying breakpoints results"""
    def __init__(self, parent):
        super(ExpressionsList, self).__init__(parent)

        # Setup
        self.InsertColumn(0, _("Expression"))
        self.InsertColumn(1, _("Value"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnItemEdited)
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def OnItemEdited(self, evt):
        if evt.IsEditCancelled():
            evt.Veto()
            return
        idx = evt.GetIndex()
        newval = evt.GetLabel()
        column = evt.GetColumn()
        expression, = self._data[idx]
        self.Parent.DeleteExpression(expression)
        if column == 0:
            expression = newval
        enabled = self.IsChecked(idx)
        self.Parent.SetExpression(expression, enabled)
        self._data[idx] = [unicode(expression),]
        self.Evaluate(enabled, expression, idx)        
        if expression:
            idx = idx + 1
            if idx == len(self._data):
                self._data[idx] = [u""]
                self.Append(self._data[idx] + [u""])

    def OnCheckItem(self, idx, enabled):
        expression, = self._data[idx]
        self.Parent.SetExpression(expression, enabled)
        self.Evaluate(enabled, expression, idx)
        if not enabled:
            self.SetStringItem(idx, 1, u"")        

    def Evaluate(self, enabled, expression, idx):
        if not enabled or not expression:
            return
        worker = RunProcInThread("Expr", self.fillexpressionvalue, \
                                 RPDBDEBUGGER.evaluate, expression)
        worker.pass_parameter(idx)
        worker.start()
    
    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of expressions

        """
        exprText = _("Expression")
        minLText = max(self.GetTextExtent(exprText)[0], self.GetColumnWidth(0))
        self._data = {}
        idx = 0
        for expression in data:
            enabled = data[expression]
            self._data[idx] = [unicode(expression),]
            self.Evaluate(enabled, expression, idx)
            
            minLText = max(minLText, self.GetTextExtent(expression)[0])
            self.Append(self._data[idx] + [u""])
            self.SetItemData(idx, idx)
            self.CheckItem(idx, enabled)
            idx += 1
        self._data[idx] = [u""]        
        self.Append(self._data[idx] + [u""])
        self.SetColumnWidth(0, minLText)

    def fillexpressionvalue(self, res, idx):
        if not res:
            return
        value, w, error = res
        if error:
            value = error
        self.SetStringItem(idx, 1, unicode(value))        

    def clearexpressionvalues(self):
        for idx in range(len(self._data)):
            self.SetStringItem(idx, 1, u"")
        
    @staticmethod
    def _printListCtrl(ctrl):
        for row in range(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
