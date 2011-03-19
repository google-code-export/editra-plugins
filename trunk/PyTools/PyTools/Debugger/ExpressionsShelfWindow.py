# -*- coding: utf-8 -*-
# Name: ExpressionsShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx
from wx.stc import STC_INDIC_PLAIN
import copy

# Editra Libraries
import util
import eclib
import ed_msg
from profiler import Profile_Get, Profile_Set
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.ExpressionsList import ExpressionsList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class ExpressionsShelfWindow(BaseShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(ExpressionsShelfWindow, self).__init__(parent)
        ctrlbar = self.setup(ExpressionsList(self))
        ctrlbar.AddStretchSpacer()
        self.layout("Clear", self.OnClear)

        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        
        # Attributes
        self.expressions = config.get(ToolConfig.TLC_EXPRESSIONS, dict())
        self._listCtrl.PopulateRows(self.expressions)
        
        RPDBDEBUGGER.restoreexpressions = self.RestoreExpressions
        RPDBDEBUGGER.saveandrestoreexpressions = self.SaveAndRestoreExpressions
        RPDBDEBUGGER.clearexpressionvalues = self._listCtrl.clearexpressionvalues

    def Unsubscription(self):
        RPDBDEBUGGER.restoreexpressions = lambda:None
        RPDBDEBUGGER.saveandrestoreexpressions = lambda:None
        RPDBDEBUGGER.clearexpressionvalues = lambda:None
        
    def DeleteExpression(self, expression):
        if not expression in self.expressions:
            return None
        del self.expressions[expression]
        self.SaveExpressions()
        
    def SetExpression(self, expression, enabled):
        self.expressions[expression] = enabled
        self.SaveExpressions()
                
    def RestoreExpressions(self):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(self.expressions)
        self._listCtrl.RefreshRows()

    def SaveExpressions(self):
        RPDBDEBUGGER._config[ToolConfig.TLC_EXPRESSIONS] = copy.deepcopy(self.expressions)

    def SaveAndRestoreExpressions(self):
        self.SaveExpressions()
        self.RestoreExpressions()
    
    def OnClear(self, evt):
        self.expressions = {}
        self.SaveAndRestoreExpressions()
        Profile_Set(ToolConfig.PYTOOL_CONFIG, RPDBDEBUGGER._config)
