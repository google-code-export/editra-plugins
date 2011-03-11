# -*- coding: utf-8 -*-
# Name: VariablesShelfWindows.py
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
import threading
import wx

# Editra Libraries
import util
import eclib
import ed_msg

# Local imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.VariablesLists import VariablesList
from PyTools.Debugger import RPDBDEBUGGER
import rpdb2

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class BaseVariablesShelfWindow(BaseShelfWindow):
    def __init__(self, parent, listtype, filterlevel, buttontitle="Unused"):
        """Initialize the window"""
        super(BaseVariablesShelfWindow, self).__init__(parent)
        self.listtype = listtype
        ctrlbar = self.setup(VariablesList(self, listtype, filterlevel))
        ctrlbar.AddStretchSpacer()
        self.layout(buttontitle, self.OnTask)
        
        # attributes
        self.filterlevel = filterlevel
        self.buttontitle = buttontitle
        self.key = None

    def UpdateVariablesList(self, variables):
        self._listCtrl.Clear()
        self._listCtrl.PopulateRows(variables)
        self._listCtrl.Refresh()

    def Unsubscription(self):
        pass

    def OnTask(self, event):
        pass
        
    def update_namespace(self, key, expressionlist):
        old_key = self.key
        old_expressionlist = self._listCtrl.get_expression_list()

        if key == old_key:
            expressionlist = old_expressionlist

        self.key = key

        if expressionlist is None:
            expressionlist = [(self.listtype, True)]

        namespace = RPDBDEBUGGER.get_namespace(expressionlist, self.filterlevel)
        if namespace:
            self.UpdateVariablesList(namespace)
        return (old_key, old_expressionlist)

class LocalVariablesShelfWindow(BaseVariablesShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(LocalVariablesShelfWindow, self).__init__(parent, u"locals()", 0)

        # Attributes
        RPDBDEBUGGER.clearlocalvariables = self._listCtrl.Clear
        RPDBDEBUGGER.updatelocalvariables = self.update_namespace
        
class GlobalVariablesShelfWindow(BaseVariablesShelfWindow):
    def __init__(self, parent):
        """Initialize the window"""
        super(GlobalVariablesShelfWindow, self).__init__(parent, u"globals()", 0)

        # Attributes
        RPDBDEBUGGER.clearglobalvariables = self._listCtrl.Clear
        RPDBDEBUGGER.updateglobalvariables = self.update_namespace
        
class ExceptionsShelfWindow(BaseVariablesShelfWindow):
    ANALYZELBL = "Analyze Exception"
    STOPANALYZELBL = "Stop Analysis"

    def __init__(self, parent):
        """Initialize the window"""
        super(ExceptionsShelfWindow, self).__init__(parent, u"rpdb_exception_info", 0, self.ANALYZELBL)

        # Attributes
        RPDBDEBUGGER.clearexceptions = self._listCtrl.Clear
        RPDBDEBUGGER.updateexceptions = self.update_namespace
        RPDBDEBUGGER.catchunhandledexception = self.UnhandledException
        
    def UnhandledException(self):
        dlg = wx.MessageDialog(self, "An unhandled exception was caught. Would you like to analyze it?",\
        "Warning", wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res != wx.ID_YES:
            RPDBDEBUGGER.do_go()
            return

        RPDBDEBUGGER.set_analyze(True)
        self.buttontitle = self.STOPANALYZELBL
        self.taskbtn.SetLabel(self.buttontitle)
        
    def OnTask(self, event):
        if self.buttontitle == self.ANALYZELBL:
            RPDBDEBUGGER.set_analyze(True)
            self.buttontitle = self.STOPANALYZELBL
            self.taskbtn.SetLabel(self.buttontitle)
        else:
            RPDBDEBUGGER.set_analyze(False)
            self.buttontitle = self.ANALYZELBL
            self.taskbtn.SetLabel(self.buttontitle)
