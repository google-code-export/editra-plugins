# -*- coding: utf-8 -*-
# Name: DebugShelfWindow.py
# Purpose: Debugger plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id $"
__revision__ = "$Revision $"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx
import copy

# Editra Libraries
import util
import eclib
import ed_msg
from profiler import Profile_Get, Profile_Set
from syntax import syntax
import syntax.synglob as synglob

# Local imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Debugger.DebuggeeWindow import DebuggeeWindow
from PyTools.Debugger.PythonDebugger import PythonDebugger
from PyTools.Debugger import RPDBDEBUGGER

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class MessageHandler(object):
    """Module Message Handler"""
    def __init__(self):
        """Initialize"""
        super(MessageHandler, self).__init__()

        # Attributes
        self.editor = None
        self._prevfile = u""
        RPDBDEBUGGER._config = Profile_Get(ToolConfig.PYTOOL_CONFIG, default=dict())
        RPDBDEBUGGER.conflictingmodules = self.ConflictingModules
        RPDBDEBUGGER.clearstepmarker = self.ClearStepMarker
        RPDBDEBUGGER.setstepmarker = self.SetStepMarker
        RPDBDEBUGGER.restorestepmarker = self.RestoreStepMarker

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)

    def Unsubscription(self):
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)
        RPDBDEBUGGER.conflictingmodules = lambda x:None
        RPDBDEBUGGER.clearstepmarker = lambda:None
        RPDBDEBUGGER.setstepmarker = lambda x,y:None
        RPDBDEBUGGER.restorestepmarker = lambda x:None      

    def ConflictingModules(self, moduleslist):
        dlg = wx.MessageDialog(self, 
        _("The modules: %s, which are incompatible with the debugger were "
        "detected and can possibly cause the debugger to fail.") % moduleslist,
        _("Warning"), wx.OK|wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()
        
    def ClearStepMarker(self):
        if self.editor:
            self.editor.ShowStepMarker(1, show=False)
            self.editor = None
        
    def SetStepMarker(self, fileName, lineNo):
        self.editor = PyToolsUtils.GetEditorOrOpenFile(self._mw, fileName)
        self.editorlineno = lineNo - 1
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    def RestoreStepMarker(self, editor):
        if self.editor != editor:
            return
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    # override in children
    def OnEditorUpdate(self, ispython, editor, force):
        pass
        
    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        filename = os.path.normcase(editor.GetFileName())
        self.OnEditorUpdate(ispython, filename, force)
        self._prevfile = filename
        if RPDBDEBUGGER.saveandrestorebreakpoints:
            RPDBDEBUGGER.saveandrestorebreakpoints()
        if RPDBDEBUGGER.saveandrestoreexpressions:
            RPDBDEBUGGER.saveandrestoreexpressions()
        self.RestoreStepMarker(editor)
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
