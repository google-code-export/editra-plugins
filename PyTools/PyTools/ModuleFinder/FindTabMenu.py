# -*- coding: utf-8 -*-
# Name: FindTabMenu.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Find Tab Menu"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx

# Editra Libraries
import util
import eclib
import ed_msg
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

ID_COPY_MODULEPATH = wx.NewId()
#-----------------------------------------------------------------------------#

class FindTabMenu(object):
    def __init__(self):
        # Editra Message Handlers
        ed_msg.Subscribe(self.OnTabMenu, ed_msg.EDMSG_UI_NB_TABMENU)

    def Unsubscription(self):
        ed_msg.Unsubscribe(self.OnTabMenu)

    def OnTabMenu(self, msg):
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            langid = getattr(editor, 'GetLangId', lambda: -1)()
            ispython = langid == synglob.ID_LANG_PYTHON
            if ispython:
                contextmenumanager = msg.GetData()
                menu = contextmenumanager.GetMenu()
                menu.Append(ID_COPY_MODULEPATH, _("Copy Module Path"))
                contextmenumanager.AddHandler(ID_COPY_MODULEPATH, self.copy_module_path)

    def copy_module_path(self, editor, evt):
        path = os.path.normcase(editor.GetFileName())
        if path is not None:
            childPath, _ = PyToolsUtils.get_packageroot(path)
            modulepath = PyToolsUtils.get_modulepath(childPath)
            util.SetClipboardText(modulepath)
