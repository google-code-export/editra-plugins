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
from PyStudio.Common import ToolConfig
from PyStudio.Common import Images
from PyStudio.Common.PyStudioUtils import PyStudioUtils
from PyStudio.Common.PyStudioUtils import RunProcInThread
from PyStudio.Common.BaseShelfWindow import BaseShelfWindow
from PyStudio.Debugger.VariablesLists import VariablesList
from PyStudio.Debugger.RpdbDebugger import RpdbDebugger

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
        # NOTE: page order must be kept in sync with this map
        self.pmap = { 0 : (ToolConfig.TLC_LOCALS_FILTERLEVEL, self._locals),
                 1 : (ToolConfig.TLC_GLOBALS_FILTERLEVEL, self._globals),
                 2 : (ToolConfig.TLC_EXCEPTIONS_FILTERLEVEL, self._exceptions)
               }
        ctrlbar = self.setup(self._nb, self._locals,
                             self._globals, self._exceptions)
        self.refreshbtn = self.AddPlateButton(u"", ed_glob.ID_REFRESH, wx.ALIGN_LEFT)
        self.refreshbtn.ToolTip = wx.ToolTip(_("Refresh Variables"))
        ctrlbar.AddStretchSpacer()
        self.filterlevel = wx.Choice(ctrlbar, wx.ID_ANY,
                                     choices=(_("Off"), _("Medium"), _("Maximum")))
        self.filterlevel.SetSelection(localsfilterlevel)
        text = wx.StaticText(ctrlbar, label=_("Filtering:"))
        ctrlbar.AddControl(text, wx.ALIGN_RIGHT)
        self.search = eclib.CommandEntryBase(ctrlbar, style=wx.TE_PROCESS_ENTER)
        self.search.Enable(True)
        self.search.SetDescriptiveText(u"Enter Regular Expression")
        self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)
        ctrlbar.AddControl(self.search, wx.ALIGN_RIGHT, 2)
        ctrlbar.AddControl(self.filterlevel, wx.ALIGN_RIGHT)
        self.layout(self.ANALYZELBL, self.OnAnalyze)
        self.taskbtn.SetBitmap(Images.Inspect.Bitmap)

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
        self.Bind(eclib.EVT_SB_PAGE_CHANGED, self.OnPageChanged, self._nb)
        self.Bind(wx.EVT_BUTTON, self.OnRefresh, self.refreshbtn)
        self.Bind(wx.EVT_CHOICE, self.OnSetFilterLevel, self.filterlevel)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnRefresh, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)

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

    def OnThemeChanged(self, msg):
        """Update Icons"""
        super(VariablesShelfWindow, self).OnThemeChanged(msg)
        self._InitImageList()
        # Update children
        for pgnum in range(self._nb.GetPageCount()):
            page = self._nb.GetPage(pgnum)
            getattr(page, 'SetupImageList', lambda:None)()

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
        """Update the persisted configuration information"""
        config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        config[key] = value
        Profile_Set(ToolConfig.PYTOOL_CONFIG, config)
        RpdbDebugger().update_namespace()

    def OnPageChanged(self, evt):
        """Update ControlBar based on current selected page"""
        cpage = self._nb.GetPage(evt.GetSelection())
        self.search.SetValue(cpage.FilterVar)
        self.filterlevel.SetSelection(cpage.FilterLevel)
        cpage.setcolumnwidths()

    def OnSetFilterLevel(self, evt):
        """Update the filter level for the current display"""
        cpage = self._nb.GetSelection()
        if cpage in self.pmap:
            cfgkey, lst = self.pmap.get(cpage)
            cur_sel = evt.GetSelection()
            lst.FilterLevel = cur_sel
            self.UpdateConfig(cfgkey, cur_sel)

    def OnRefresh(self, event):
        """Search for variables according to the text from the text control"""
        cpage = self._nb.GetSelection()
        if cpage in self.pmap:
            cfgkey, lst = self.pmap.get(cpage)
            lst.FilterVar = self.search.GetValue()
            RpdbDebugger().update_namespace()
       
    def OnCancelSearch(self, event):
        """Clear the text from the text control"""
        self.search.SetValue("")
        cpage = self._nb.GetSelection()
        if cpage in self.pmap:
            cfgkey, lst = self.pmap.get(cpage)
            lst.FilterVar = ""
            RpdbDebugger().update_namespace()
