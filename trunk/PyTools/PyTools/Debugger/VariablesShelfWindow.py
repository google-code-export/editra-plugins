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
from PyTools.Debugger.RpdbDebugger import RpdbDebugger

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
        bstyle = eclib.SEGBOOK_STYLE_NO_DIVIDERS|eclib.SEGBOOK_STYLE_LEFT
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
        self.filterlevellocals = wx.Choice(ctrlbar, wx.ID_ANY,
                                           choices=self.FILTER_LEVELS)
        self.filterlevellocals.SetStringSelection(self.FILTER_LEVELS[localsfilterlevel])
        self.filterlevelglobals = wx.Choice(ctrlbar, wx.ID_ANY,
                                            choices=self.FILTER_LEVELS)
        self.filterlevelglobals.SetStringSelection(self.FILTER_LEVELS[globalsfilterlevel])
        self.filterlevelexceptions = wx.Choice(ctrlbar, wx.ID_ANY,
                                               choices=self.FILTER_LEVELS)
        self.filterlevelexceptions.SetStringSelection(self.FILTER_LEVELS[exceptionsfilterlevel])
        text = wx.StaticText(ctrlbar, label=_("Filter Levels:"))
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddSpacer(20,-1)
        text = wx.StaticText(ctrlbar, label=_("Locals:"))
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevellocals, wx.ALIGN_RIGHT)
        text = wx.StaticText(ctrlbar, wx.ID_ANY, _("Globals:"))
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevelglobals, wx.ALIGN_RIGHT)
        text = wx.StaticText(ctrlbar, wx.ID_ANY, _("Exceptions:"))
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        ctrlbar.AddControl(self.filterlevelexceptions, wx.ALIGN_RIGHT)
        self.layout(self.ANALYZELBL, self.OnAnalyze)

        # Debugger attributes
        RpdbDebugger().clearlocalvariables = self._locals.Clear
        RpdbDebugger().updatelocalvariables = self._locals.update_namespace
        RpdbDebugger().clearglobalvariables = self._globals.Clear
        RpdbDebugger().updateglobalvariables = self._globals.update_namespace
        RpdbDebugger().clearexceptions = self._exceptions.Clear
        RpdbDebugger().updateexceptions = self._exceptions.update_namespace
        RpdbDebugger().catchunhandledexception = self.UnhandledException
        RpdbDebugger().updateanalyze = self.UpdateAnalyze
        
        # Event Handlers
        self.Bind(wx.EVT_CHOICE, self.SetFilterLevelLocals, self.filterlevellocals)
        self.Bind(wx.EVT_CHOICE, self.SetFilterLevelGlobals, self.filterlevelglobals)
        self.Bind(wx.EVT_CHOICE, self.SetFilterLevelExceptions, self.filterlevelexceptions)

        RpdbDebugger().update_namespace()

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
        RpdbDebugger().clearlocalvariables = lambda:None
        RpdbDebugger().updatelocalvariables = lambda x,y:(None,None)
        RpdbDebugger().clearglobalvariables = lambda:None
        RpdbDebugger().updateglobalvariables = lambda x,y:(None,None)
        RpdbDebugger().clearexceptions = lambda:None
        RpdbDebugger().updateexceptions = lambda x,y:(None,None)
        RpdbDebugger().unhandledexception = False
        RpdbDebugger().catchunhandledexception = lambda:None
        RpdbDebugger().updateanalyze = lambda:None

    def UnhandledException(self):
        RpdbDebugger().unhandledexception = True
        wx.CallAfter(self._unhandledexception)

    def _unhandledexception(self):
        dlg = wx.MessageDialog(self,
                               _("An unhandled exception was caught. Would you like to analyze it?"),
                               _("Warning"),
                               wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res != wx.ID_YES:
            RpdbDebugger().unhandledexception = False
            RpdbDebugger().do_go()
        else:
            RpdbDebugger().set_analyze(True)

    def OnAnalyze(self, event):
        if self.taskbtn.GetLabel() == self.ANALYZELBL:
            RpdbDebugger().set_analyze(True)
        else:
            RpdbDebugger().set_analyze(False)

    def UpdateAnalyze(self):
        if RpdbDebugger().analyzing:
            self.taskbtn.SetLabel(self.STOPANALYZELBL)
        else:
            self.taskbtn.SetLabel(self.ANALYZELBL)

    def UpdateConfig(self, key, value):
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[key] = value
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
        RpdbDebugger().update_namespace()
    
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
        