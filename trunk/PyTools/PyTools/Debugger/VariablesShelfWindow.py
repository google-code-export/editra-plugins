# -*- coding: utf-8 -*-
# Name: VariablesShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import threading
import wx

# Editra Libraries
import ed_glob
import eclib
from profiler import Profile_Get, Profile_Set

# Local imports
from PyTools.Common import ToolConfig
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
    FILTER_LEVELS = ('0:Off', '1:Medium', '2:Maximum')
    
    def __init__(self, parent):
        """Initialize the window"""
        super(VariablesShelfWindow, self).__init__(parent)

        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        localsfilterlevel = config.get(ToolConfig.TLC_LOCALS_FILTERLEVEL, 0)
        globalsfilterlevel = config.get(ToolConfig.TLC_GLOBALS_FILTERLEVEL, 0)
        exceptionsfilterlevel = config.get(ToolConfig.TLC_EXCEPTIONS_FILTERLEVEL, 0)
        
        # Attributes
        bstyle = eclib.SEGBOOK_STYLE_NO_DIVIDERS|\
                 eclib.SEGBOOK_STYLE_LEFT
        self._nb = eclib.SegmentBook(self, style=bstyle)
        self._locals = VariablesList(self._nb, self.LOCALSSTR, localsfilterlevel)
        self._globals = VariablesList(self._nb, self.GLOBALSSTR, globalsfilterlevel)
        self._exceptions = VariablesList(self._nb, self.EXCEPTIONSSTR, exceptionsfilterlevel)
        
        # Setup
        self._InitImageList()
        self._nb.AddPage(self._locals, _("Locals"), img_id=0)
        self._nb.AddPage(self._globals, _("Globals"), img_id=1)
        self._nb.AddPage(self._exceptions, _("Exceptions"), img_id=2)
        ctrlbar = self.setup(self._nb, self._locals,
                             self._globals, self._exceptions)
        ctrlbar.AddStretchSpacer()
        self.filterlevellocals = wx.ComboBox(ctrlbar, wx.ID_ANY, \
        value=self.FILTER_LEVELS[localsfilterlevel], choices=self.FILTER_LEVELS, style=wx.CB_READONLY|eclib.PB_STYLE_NOBG)
        self.filterlevelglobals = wx.ComboBox(ctrlbar, wx.ID_ANY, \
        value=self.FILTER_LEVELS[globalsfilterlevel], choices=self.FILTER_LEVELS, style=wx.CB_READONLY|eclib.PB_STYLE_NOBG)
        self.filterlevelexceptions = wx.ComboBox(ctrlbar, wx.ID_ANY, \
        value=self.FILTER_LEVELS[exceptionsfilterlevel], choices=self.FILTER_LEVELS, style=wx.CB_READONLY|eclib.PB_STYLE_NOBG)
        text = wx.StaticText(ctrlbar, wx.ID_ANY, "Filter Levels           Locals")
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevellocals, wx.ALIGN_RIGHT)
        text = wx.StaticText(ctrlbar, wx.ID_ANY, "Globals")
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevelglobals, wx.ALIGN_RIGHT)
        text = wx.StaticText(ctrlbar, wx.ID_ANY, "Exceptions")
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevelexceptions, wx.ALIGN_RIGHT)
        self.layout(self.ANALYZELBL, self.OnAnalyze)

        # Debugger attributes
        RPDBDEBUGGER.clearlocalvariables = self._locals.Clear
        RPDBDEBUGGER.updatelocalvariables = self._locals.update_namespace
        RPDBDEBUGGER.clearglobalvariables = self._globals.Clear
        RPDBDEBUGGER.updateglobalvariables = self._globals.update_namespace
        RPDBDEBUGGER.clearexceptions = self._exceptions.Clear
        RPDBDEBUGGER.updateexceptions = self._exceptions.update_namespace
        RPDBDEBUGGER.catchunhandledexception = self.UnhandledException
        RPDBDEBUGGER.updateanalyze = self.UpdateAnalyze
        
        # Event Handlers
        self.Bind(wx.EVT_COMBOBOX, self.SetFilterLevelLocals, self.filterlevellocals)
        self.Bind(wx.EVT_COMBOBOX, self.SetFilterLevelGlobals, self.filterlevelglobals)
        self.Bind(wx.EVT_COMBOBOX, self.SetFilterLevelExceptions, self.filterlevelexceptions)

        RPDBDEBUGGER.update_namespace()

    def _InitImageList(self):
        """Initialize the segmentbooks image list"""
        dorefresh = False
        if len(self._imglst):
            del self._imglst
            self._imglst = list()
            dorefresh = True

        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_VARIABLE_TYPE), wx.ART_MENU)
        self._imglst.append(bmp)
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_WEB), wx.ART_MENU)
        self._imglst.append(bmp)
        bmp = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MENU)
        self._imglst.append(bmp)
        self._nb.SetImageList(self._imglst)
        self._nb.SetUsePyImageList(True)

        if dorefresh:
            self._nb.Refresh()

    def Unsubscription(self):
        """Cleanup on Destroy"""
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
        dlg = wx.MessageDialog(self,
                               _("An unhandled exception was caught. Would you like to analyze it?"),
                               _("Warning"),
                               wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res != wx.ID_YES:
            RPDBDEBUGGER.unhandledexception = False
            RPDBDEBUGGER.do_go()
        else:
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

    def UpdateConfig(self, key, value):
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[key] = value
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
        RPDBDEBUGGER.update_namespace()
    
    def SetFilterLevelLocals(self, evt):
        combocurrent_selection = self.filterlevellocals.GetSelection()
        self._locals.SetFilterLevel(combocurrent_selection)
        self.UpdateConfig(ToolConfig.TLC_LOCALS_FILTERLEVEL, combocurrent_selection)
        
    def SetFilterLevelGlobals(self, evt):
        combocurrent_selection = self.filterlevelglobals.GetSelection()
        self._globals.SetFilterLevel(combocurrent_selection)
        self.UpdateConfig(ToolConfig.TLC_GLOBALS_FILTERLEVEL, combocurrent_selection)        
        
    def SetFilterLevelExceptions(self, evt):
        combocurrent_selection = self.filterlevelexceptions.GetSelection()
        self._exceptions.SetFilterLevel(combocurrent_selection)
        self.UpdateConfig(ToolConfig.TLC_EXCEPTIONS_FILTERLEVEL, combocurrent_selection)
        