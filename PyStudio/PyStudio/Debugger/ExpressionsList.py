# -*- coding: utf-8 -*-
# Name: ExpressionsList.py
# Purpose: ModuleFinder plugin
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
from PyStudio.Common.PyStudioUtils import RunProcInThread
from PyStudio.Debugger.RpdbDebugger import RpdbDebugger

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class ExpressionsList(eclib.EToggleEditListCtrl):
    """List control for displaying breakpoints results"""

    COL_EXPR = 0
    COL_VALUE = 1
    
    def __init__(self, parent):
        super(ExpressionsList, self).__init__(parent)

        # Attributes
        self._data = {}
        
        # Setup
        self.colname_expr = _("Expression")
        self.colname_value = _("Value")
    
        self.InsertColumn(ExpressionsList.COL_EXPR, self.colname_expr)
        self.InsertColumn(ExpressionsList.COL_VALUE, self.colname_value)

        # Event Handlers
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.OnItemEdited)
        
    def set_mainwindow(self, mw):
        self._mainw = mw

    def GetSelectedExpressions(self):
        """Get a list of selected breakpoints
        @return: [(fname, line, expr),]

        """
        rval = list()
        for index in self.GetSelections():
            rval.append(self.GetRowData(index))
        return rval

    def OpenEditor(self, col, row):
        if col == 0:
            super(ExpressionsList, self).OpenEditor(col, row)
    
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
                                 RpdbDebugger().evaluate, expression)
        worker.pass_parameter(idx)
        worker.start()
    
    def Clear(self):
        """Delete all the rows """
        self.DeleteAllItems()

    def PopulateRows(self, data):
        """Populate the list with the data
        @param data: dictionary of expressions

        """
        if not data:
            return
        self._data = {}
        idx = 0
        for expression in data:
            enabled = data[expression]
            self._data[idx] = [unicode(expression),]
            self.Evaluate(enabled, expression, idx)
            
            self.Append(self._data[idx] + [u""])
            self.SetItemData(idx, idx)
            self.CheckItem(idx, enabled)
            idx += 1

        self.SetColumnWidth(ExpressionsList.COL_EXPR, wx.LIST_AUTOSIZE)
        exprcolwidth = max(self.GetTextExtent(self.colname_expr + "          ")[0], self.GetColumnWidth(ExpressionsList.COL_EXPR))
        self.SetColumnWidth(ExpressionsList.COL_EXPR, exprcolwidth)

    def fillexpressionvalue(self, res, idx):
        if not res:
            return
        value, w, error = res
        if error:
            value = error
        self.SetStringItem(idx, 1, unicode(value))        

    def clearexpressionvalues(self):
        if not self._data:
            return
        for idx in range(len(self._data)):
            self.SetStringItem(idx, 1, u"")
        
    @staticmethod
    def _printListCtrl(ctrl):
        for row in range(0, ctrl.GetItemCount()):
            for column in xrange(0, ctrl.GetColumnCount()):
                print ctrl.GetItem(row, column).GetText(), "\t",
            print ""
