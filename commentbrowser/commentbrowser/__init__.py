#!/usr/bin/env python
# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: CommentBrowser Plugin                                              #
# Author: DR0ID <dr0iddr0id@googlemail.com>                                   #
# Copyright: (c) 2007 DR0ID                                                   #
# Licence: wxWindows Licence                                                  #
###############################################################################
# Plugin Meta
"""Adds a Comment Browser Sidepanel"""
__author__ = "DR0ID"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import wx.aui

# Libs from Editra
import iface
import plugin

# Local imports
import cbrowser

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Interface implementation
class CommentBrowserPanel(plugin.Plugin):
    """Adds a commentbrowser to the view menu"""
    
    plugin.Implements(iface.MainWindowI)
    
    def PlugIt(self, parent):
        """ Adds the view menu entry and registers the event handler"""
        self._mainwin = parent
        self._log = wx.GetApp().GetLog()
        if self._mainwin != None:
            self._log("[commentbrowser] Installing commentbrowser plugin")
            self._commentbrowser = cbrowser.CBrowserPane(self._mainwin, 
                                                    cbrowser.ID_CBROWSERPANE)
            mgr = self._mainwin.GetFrameManager()
            mgr.AddPane(self._commentbrowser, 
                        wx.aui.AuiPaneInfo().Name(cbrowser.PANE_NAME).\
                        Caption("Comment Browser").Bottom().Layer(1).\
                        CloseButton(True).MaximizeButton(True).\
                        BestSize(wx.Size(-1, 350)))
            mgr.Update()
            pane = mgr.GetPane(cbrowser.PANE_NAME)
            if pane.IsShown():
                pane.window._mi.Check(True)
            else:
                pane.window._mi.Check(False)
            
            
    def GetMenuHandlers(self):
        """Pass event handler for menu item to main window for management"""
        # TODO: implement
        return [(cbrowser.ID_COMMENTBROWSE, self._commentbrowser.OnShow)]

    def GetUIHandlers(self):
        """Pass Ui handlers to main window for management"""
        return list()
