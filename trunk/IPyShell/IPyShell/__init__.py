# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: IPythonShell Plugin                                                #
# Author: Laurent Dufréchou <laurent.dufrechou@gmail.com>                     #
# Copyright: (c) 2008 Laurent Dufréchou                                       #
# License: wxWindows License                                                  #
###############################################################################
# Plugin Metadata
"""Adds an IPythonShell to the Shelf"""
__author__ = "Laurent Dufrechou"
__version__ = "0.3"

#-----------------------------------------------------------------------------#
# Imports

import wx,sys
import iface
import plugin

import profiler

#used for ipython GUI objects
from IPython.gui.wx.ipython_view import IPShellWidget
from IPython.gui.wx.ipython_history import IPythonHistoryPanel

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Interface Implementation
class IPyShell(plugin.Plugin):
    """Adds a PyShell to the Shelf"""
    plugin.Implements(iface.ShelfI)
    ID_IPYSHELL = wx.NewId()
    __name__ = u'IPyShell'

    def AllowMultiple(self):
        """IPythonShell allows multiple instances"""
        return True

    def OptionSave(self,key,value):
        profiler.Profile_Set('IPython.'+key, value)
        
    def CreateItem(self, parent):
        """Returns an IPythonShell Panel"""
        self._log = wx.GetApp().GetLog()
        self._log("[IPyShell][info] Creating IPythonShell instance for Shelf")
        #main_win = wx.GetApp().GetMainWindow()
        #parent.AddPage(self.history_panel,'IPythonHistory',False)
        
        splitter = wx.SplitterWindow(parent, -1, style = wx.SP_LIVE_UPDATE)
        
        self.history_panel    = IPythonHistoryPanel(splitter)
        self.ipython_panel    = IPShellWidget(splitter, background_color="BLACK")
                                              #user_ns=locals(),user_global_ns=globals(),)
        self.ipython_panel.setOptionTrackerHook(self.OptionSave)
        self.ipython_panel.setHistoryTrackerHook(self.history_panel.write)
        
        options = self.ipython_panel.getOptions()
        for key in options.keys():
            saved_value = profiler.Profile_Get('IPython.'+key)
            if saved_value is not None:
                options[key]['value'] = saved_value
        
        self.ipython_panel.reloadOptions(options)

        splitter.SetMinimumPaneSize(20)
        splitter.SplitVertically(self.ipython_panel, self.history_panel, -100)

        return splitter

        self._log("[IPyShell][info] IPythonShell succesfully created")
        return self.ipython_panel

    def GetId(self):
        return IPyShell.ID_IPYSHELL

    def GetMenuEntry(self, menu):
        return wx.MenuItem(menu, IPyShell.ID_IPYSHELL,
                           IPyShell.__name__, 
                           _("Open an IPython Shell"))

    def GetName(self):
        return IPyShell.__name__

    def IsStockable(self):
        return True
