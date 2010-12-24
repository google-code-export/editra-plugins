# -*- coding: utf-8 -*-
# Name: __init__.py                                                           
# Purpose: Pylint plugin                                              
# Author: Mike Rans                              
# Copyright: (c) 2010 Mike Rans                                
# License: wxWindows License                                                  
###############################################################################

# Plugin Metadata
"""
Adds Python syntax checking using Pylint with results in a Shelf window.

"""

__version__ = "0.1"
__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import sys
import wx

# Editra imports
import ed_glob
import iface
import plugin
import util

# Local Imports
from openmodule import OpenModuleDialog, ID_OPEN_MODULE
from profiler import Profile_Get, Profile_Set
from SyntaxCheckWindow import SyntaxCheckWindow
import ToolConfig
import finder
import ptcfg

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation
PYTOOLS_PREFS = 'PyTools.Prefs'
PYTOOLS_BASE_PATH_CHOOSE_MSG  = _("Select Python library directory (ex: %s): ")
PYTOOLS_BASE_PATH_INVALID_MSG = _("""%s doesn't appear to be valid. 
The selected directory should contain the site-packages subdirectory""")

#-----------------------------------------------------------------------------#
# Implementation
class pytools(plugin.Plugin):
    """Script Launcher and output viewer"""
    plugin.Implements(iface.ShelfI)
    ID_PYTOOLS = wx.NewId()
    INSTALLED = False
    SHELF = None

    @property
    def __name__(self):
        return u'pytools'

    def AllowMultiple(self):
        """pytools allows multiple instances"""
        return True

    def CreateItem(self, parent):
        """Create a pytools panel"""
        util.Log("[pytools][info] Creating pytools instance for Shelf")
        return SyntaxCheckWindow(parent)

    def GetBitmap(self):
        """Get the tab bitmap
        @return: wx.Bitmap

        """
        bmp = wx.ArtProvider.GetBitmap(str(ed_glob.ID_BIN_FILE), wx.ART_MENU)
        return bmp

    def GetId(self):
        """The unique identifier of this plugin"""
        return self.ID_PYTOOLS

    def GetMenuEntry(self, menu):
        """This plugins menu entry"""
        item = wx.MenuItem(menu, self.ID_PYTOOLS, self.__name__,
                           _("Show pytools"))
        item.SetBitmap(self.GetBitmap())
        return item

    def GetMinVersion(self):
        """Minimum version of Editra this plugin is compatible with"""
        return "5.99"

    def GetName(self):
        """The name of this plugin"""
        return self.__name__

    def InstallOpenModule(self, parent):
        util.Log("[pytools][info] Installing module opener")
        file_menu = parent.GetMenuBar().GetMenuByName("file")
        # Insert the Open Module command before Open Recent
        # TODO: Find the 'open recent' position in a more generic way
        # NOTE:CJP you can use the FindById method of wxMenu to do this
        file_menu.Insert(4, ID_OPEN_MODULE,
                _("Open Python &Module\tCtrl+Shift+M"),
                _("Open the source code of a Python module from sys.path"))

    def InstallComponents(self, mainw):
        """Install extra menu components
        param mainw: MainWindow Instance

        """
        self._finder = None
        self.InstallOpenModule(mainw)
        mainw.AddMenuHandler(ID_OPEN_MODULE, self.OnOpenModule)
            
    def IsInstalled(self):
        """Check whether pytools has been installed yet or not
        @note: overridden from Plugin
        @return bool

        """
        return pytools.INSTALLED

    def IsStockable(self):
        """This item can be reloaded between sessions"""
        return True

    def OnOpenModule(self, evt):
        """Show the OpenModule dialog"""
        if evt.GetId() != ID_OPEN_MODULE:
            evt.Skip()

        win = wx.GetApp().GetActiveWindow()

        if self._finder == None:
            prefs = Profile_Get(PYTOOLS_PREFS, default=dict())
            base = prefs.get('module_base')
            if not base or not CheckModuleBase(base):
                base = ChooseModuleBase(win)
            if base:
                prefs['module_base'] = base
                util.Log("[pytools][debug] Saving base search dir: %s" % base)
                Profile_Set(PYTOOLS_PREFS, prefs)
                path = finder.GetSearchPath(base)
                util.Log("[pytools][debug] search path: %s" % path)
                self._finder = finder.ModuleFinder(path)
            else:
                return

        mdlg = OpenModuleDialog(win, self._finder, title=_("Open module"))
        mdlg.SetFocus()
        
        if mdlg.ShowModal() != wx.ID_OK:
            mdlg.Destroy()
            return

        filename = mdlg.GetValue()
        if filename:
            mdlg.Destroy()
            win.DoOpen(evt, filename)

def CheckModuleBase(base):
    if sys.platform == 'win32':
        spkg = os.path.join(base, 'lib', 'site-packages')
    else:
        spkg = os.path.join(base, 'site-packages')
    return base != None and os.path.exists(base) and os.path.isdir(base) \
            and os.path.exists(spkg)

# XXX investigate python installation layout on MacOSX ("apple python" vs. 
# default python install
def ChooseModuleBase(parent):
    """Shows a dialog to choose the python libraries directory.
    @return: the python installation libraries root (the directory containing, 
             among the others, the site-packages dir) or None if the user
             didn't make any choice or choose an invalid path
    """
    if sys.platform == 'win32':
        ex = "C:\Python26"
    elif platform.mac_ver()[0]:
        ex = "/Library/Frameworks/Python.framework/2.6"
    else:
        ex = "/usr/lib/python-2.6"

    title = PYTOOLS_BASE_PATH_CHOOSE_MSG % ex
    value = None
    dlg = wx.DirDialog(parent, title,
                       style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
    if dlg.ShowModal() == wx.ID_OK:
        value = dlg.GetPath()
        
    if not CheckModuleBase(value):
        errmsg = PYTOOLS_BASE_PATH_INVALID_MSG % value
        errdlg = wx.MessageDialog(dlg, errmsg, 
                                _('Error'),  wx.OK | wx.ICON_ERROR)
        if errdlg.ShowModal() == wx.ID_OK:
            errdlg.Destroy()
        value = None

    dlg.Destroy()
    return value

#-----------------------------------------------------------------------------#
# Configuration Interface

def GetConfigObject():
    return ConfigObject()

class ConfigObject(plugin.PluginConfigObject):
    """Plugin configuration object for pytools
    Provides configuration panel for plugin dialog.

    """
    def GetConfigPanel(self, parent):
        """Get the configuration panel for this plugin
        @param parent: parent window for the panel
        @return: wxPanel

        """
        return ToolConfig.ToolConfigPanel(parent)

    def GetLabel(self):
        """Get the label for this config panel
        @return string

        """
        return _("pytools")
