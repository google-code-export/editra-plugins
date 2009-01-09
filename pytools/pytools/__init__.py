###############################################################################
# Name: __init__.py                                                           #
# Purpose: Python Tools plugin                                                #
# Author: Ofer Schwarz <os.urandom@gmail.com>                                 #
# Copyright: (c) 2008 Ofer Schwarz <os.urandom@gmail.com>                     #
# Licence: wxWindows Licence                                                  #
###############################################################################
"""
Various Python tools for Editra
"""
__author__ = "Ofer Schwarz"
__version__ = "0.1"

import wx
import iface
import plugin

from openmodule import OpenModuleDialog, ID_OPEN_MODULE

_ = wx.GetTranslation
#-----------------------------------------------------------------------------#

class PyTools(plugin.Plugin):
    """
    Adds Python tools to the Editra menus
    """
    plugin.Implements(iface.MainWindowI)

    def PlugIt(self, parent):
        """Add menu entries"""
        if parent:
            self._mw = parent
            # Use Editra's loggin system
            self._log = wx.GetApp().GetLog()
            self._log("[pytools][info] Installing Pytools")
            # Install all tools
            self.InstallOpenModule()
        else:
            self._log("[pytools][err] Failed to install pytools plugin")
            
    def InstallOpenModule(self):
        self._log("[pytools][info] Installing module opener")
        file_menu = self._mw.GetMenuBar().GetMenuByName("file")
        # Insert the Open Module command before Open Recent
        # TODO: Find the 'open recent' position in a more generic way
        file_menu.Insert(4, ID_OPEN_MODULE,
                _("Open Python &Module\tCtrl+Shift+M"), 
                _("Open the source code of a Python module from sys.path"))

    def GetMenuHandlers(self):
        """This is used to register the menu handler with the app and
        associate the event with the parent window. It needs to return
        a list of ID/Handler pairs for each menu handler that the plugin
        is providing.

        """
        return [(ID_OPEN_MODULE, self.OnOpenModule)]

    def GetUIHandlers(self):
        """This is used to register the update ui handler with the app and
        associate the event with the parent window. This plugin doesn't use
        the UpdateUI event so it can just return an empty list.

        """
        return list()
    
    def OnOpenModule(self, evt):
        if evt.GetId() != ID_OPEN_MODULE:
            evt.Skip()
        
        mdlg = OpenModuleDialog(self._mw,
                                message=_("Enter package/module name\n"
                                          "(e.g 'pickle', 'wx.lib.pyshell')"),
                                caption=_("Open module"))

        if mdlg.ShowModal() != wx.ID_OK:
            return

        filename = mdlg.GetValue()
        if filename:
            self._mw.DoOpen(evt, filename)
