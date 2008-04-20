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
import wx
#from wx.py import shell
import iface
#from profiler import Profile_Get
import plugin

from IPython.gui.wx.ipython_view import IPShellWidget

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

    def OnExitDlg(self,evt):
        pass
    
    def CreateItem(self, parent):
        """Returns an IPythonShell Panel"""
        self._log = wx.GetApp().GetLog()
        self._log("[IPyShell][info] Creating IPythonShell instance for Shelf")
        #self.history_panel    = IPythonHistoryPanel(self)
        
        self.ipython_panel    = IPShellWidget(parent, background_color="BLACK")
                                              #user_ns=locals(),user_global_ns=globals(),)
        
        #self.ipython_panel    = IPShellWidget(self,background_color = "WHITE")

        #self.ipython_panel.setHistoryTrackerHook(self.history_panel.write)
        #self.ipython_panel.setStatusTrackerHook(self.updateStatus)
        #self.ipython_panel.setAskExitHandler(self.OnExitDlg)
        #self.ipython_panel    = IPShellWidget(parent,background_color = "BLACK")
        
        #pyshell = shell.Shell(parent, locals=dict())
        #pyshell.setStyles(self.__SetupFonts())
##        main_win = wx.GetApp().GetActiveWindow()
##        my_panel = wx.Panel(main_win, wx.ID_ANY)
##        mgr = main_win.GetFrameManager()
##        mgr.AddPane(my_panel, wx.aui.AuiPaneInfo().Name("MyPanel").\
##                    Caption("My Test Panel").Left().Layer(0).\
##                    CloseButton(True).MaximizeButton(False).\
##                    BestSize(wx.Size(300, 500)
##        mgr.GetPane("MyPanel").Show()
                     
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
