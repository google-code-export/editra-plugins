# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: IPythonShell Plugin                                                #
# Author: Laurent Dufréchou <laurent.dufrechou@gmail.com>                     #
# Copyright: (c) 2008 Laurent Dufréchou                                       #
# Licence: wxWindows Licence                                                  #
###############################################################################
# Plugin Metadata
"""Adds an IPythonShell to the Shelf"""
__author__ = "Laurent Dufrechou"
__version__ = "0.1"

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
    __name__ = u'IPythonShell'

    #def __SetupFonts(self):
        #"""Create the font settings for the shell by trying to get the
        #users prefered font settings used in the EdStc
        #"""
        #fonts = { 
        #          'size'      : 11,
        #          'lnsize'    : 10,
        #          'backcol'   : '#FFFFFF',
        #          'calltipbg' : '#FFFFB8',
        #          'calltipfg' : '#404040',
        #}

        #font = Profile_Get('FONT1', 'font', wx.Font(11, wx.FONTFAMILY_MODERN, 
        #                                                wx.FONTSTYLE_NORMAL, 
        #                                                wx.FONTWEIGHT_NORMAL))
        #if font.IsOk() and len(font.GetFaceName()):
        #    fonts['mono'] = font.GetFaceName()
        #    fonts['size'] = font.GetPointSize()
        #    if fonts['size'] < 11:
        #        fonts['size'] = 11
        #    fonts['lnsize'] = fonts['size'] - 1

        #font = Profile_Get('FONT2', 'font', wx.Font(11, wx.FONTFAMILY_SWISS, 
        #                                                wx.FONTSTYLE_NORMAL, 
        #                                                wx.FONTWEIGHT_NORMAL))
        #if font.IsOk() and len(font.GetFaceName()):
        #    fonts['times'] = font.GetFaceName()
        #    fonts['helv'] = font.GetFaceName()
        #    fonts['other'] = font.GetFaceName()

        #return fonts

    def AllowMultiple(self):
        """IPythonShell allows multiple instances"""
        return True

    def OnExitDlg(self,evt):
        pass
    
    def CreateItem(self, parent):
        """Returns an IPythonShell Panel"""
        self._log = wx.GetApp().GetLog()
        self._log("[IPyShell][info] Creating IPythonShell instance for Shelf")
        self.ipython_panel    = IPShellWidget(parent,background_color = "BLACK")
        
        #pyshell = shell.Shell(parent, locals=dict())
        #pyshell.setStyles(self.__SetupFonts())
        return self.ipython_panel

    def GetId(self):
        return self.ID_IPYSHELL

    def GetMenuEntry(self, menu):
        return wx.MenuItem(menu, self.ID_IPYSHELL, self.__name__, 
                                        _("Open an IPython Shell"))

    def GetName(self):
        return self.__name__

    def IsStockable(self):
        return True
