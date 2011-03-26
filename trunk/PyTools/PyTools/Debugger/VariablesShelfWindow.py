# -*- coding: utf-8 -*-
# Name: VariablesShelfWindow.py
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
import eclib

# Local imports
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Common.BaseShelfWindow import BaseShelfWindow
from PyTools.Debugger.VariablesLists import VariablesList
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class VariablesShelfWindow(BaseShelfWindow):
    LOCALSSTR = u"locals()"
    GLOBALSSTR = u"globals()"
    EXCEPTIONSSTR = u"rpdb_exception_info"
    ANALYZELBL = "Analyze Exception"
    STOPANALYZELBL = "Stop Analysis"
    
    def __init__(self, parent):
        """Initialize the window"""
        super(VariablesShelfWindow, self).__init__(parent)
        bstyle = eclib.SEGBOOK_STYLE_NO_DIVIDERS|eclib.SEGBOOK_STYLE_LABELS
        self._nb = eclib.SegmentBook(self, style=bstyle)
        self._locals = VariablesList(self._nb, self.LOCALSSTR, 0)
        self._globals = VariablesList(self._nb, self.GLOBALSSTR, 0)
        self._exceptions = VariablesList(self._nb, self.EXCEPTIONSSTR, 0)
        # Setup
        self._InitImageList()
        self._nb.AddPage(self._locals, _("Locals"), img_id=0)
        self._nb.AddPage(self._globals, _("Globals"), img_id=0)
        self._nb.AddPage(self._exceptions, _("Exceptions"), img_id=0)

        ctrlbar = self.setup(self._nb, self._locals, self._globals, self._exceptions)
        ctrlbar.AddStretchSpacer()
        self.layout(self.ANALYZELBL, self.OnAnalyze)
        
        # attributes
        RPDBDEBUGGER.clearlocalvariables = self._locals.Clear
        RPDBDEBUGGER.updatelocalvariables = self._locals.update_namespace
        RPDBDEBUGGER.clearglobalvariables = self._globals.Clear
        RPDBDEBUGGER.updateglobalvariables = self._globals.update_namespace
        RPDBDEBUGGER.clearexceptions = self._exceptions.Clear
        RPDBDEBUGGER.updateexceptions = self._exceptions.update_namespace
        RPDBDEBUGGER.catchunhandledexception = self.UnhandledException
        RPDBDEBUGGER.updateanalyze = self.UpdateAnalyze

    def Unsubscription(self):
        RPDBDEBUGGER.clearlocalvariables = lambda:None
        RPDBDEBUGGER.updatelocalvariables = lambda x,y:(None,None)
        RPDBDEBUGGER.clearglobalvariables = lambda:None
        RPDBDEBUGGER.updateglobalvariables = lambda x,y:(None,None)
        RPDBDEBUGGER.clearexceptions = lambda:None
        RPDBDEBUGGER.updateexceptions = lambda x,y:(None,None)
        RPDBDEBUGGER.unhandledexception = False
        RPDBDEBUGGER.catchunhandledexception = lambda:None
        RPDBDEBUGGER.updateanalyze = lambda:None

    def UnhandledException(self):
        RPDBDEBUGGER.unhandledexception = True
        wx.CallAfter(self._unhandledexception)
        
    def _unhandledexception(self):        
        dlg = wx.MessageDialog(self, "An unhandled exception was caught. Would you like to analyze it?",\
        "Warning", wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res != wx.ID_YES:
            RPDBDEBUGGER.unhandledexception = False
            RPDBDEBUGGER.do_go()
            return

        RPDBDEBUGGER.set_analyze(True)
        
    def OnAnalyze(self, event):
        if self.taskbtn.GetLabel() == self.ANALYZELBL:
            RPDBDEBUGGER.set_analyze(True)
        else:
            RPDBDEBUGGER.set_analyze(False)

    def UpdateAnalyze(self):
        if RPDBDEBUGGER.analyzing:
            self.taskbtn.SetLabel(self.STOPANALYZELBL)
        else:
            self.taskbtn.SetLabel(self.ANALYZELBL)
