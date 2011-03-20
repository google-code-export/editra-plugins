# -*- coding: utf-8 -*-
# Name: BreakpointsMessageHandler.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Breakpoints MessageHandler"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import util
import ed_msg
from profiler import Profile_Get, Profile_Set

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class BreakpointsMessageHandler(object):
    """Module Message Handler"""
    def __init__(self):
        """Initialize"""
        super(BreakpointsMessageHandler, self).__init__()

        # Attributes
        RPDBDEBUGGER._config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        
        self.Subscription()

    def Subscription(self):
        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)
    
    def Unsubscription(self):
        Profile_Set(ToolConfig.PYTOOL_CONFIG, RPDBDEBUGGER._config)
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)

    # override in children
    def SaveAndRestoreBreakpoints(self):
        pass
        
    def UpdateForEditor(self, editor, force=False):
        self.SaveAndRestoreBreakpoints()
        Profile_Set(ToolConfig.PYTOOL_CONFIG, RPDBDEBUGGER._config)

    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        self.UpdateForEditor(editor)

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = PyToolsUtils.GetEditorForFile(self._mw, msg.GetData())
        self.UpdateForEditor(editor)

    def OnFileSave(self, msg):
        """Load File message"""
        filename, tmp = msg.GetData()
        editor = PyToolsUtils.GetEditorForFile(self._mw, filename)
        self.UpdateForEditor(editor)
