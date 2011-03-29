# -*- coding: utf-8 -*-
# Name: MessageHandler.py
# Purpose: Message Handler
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Message Handler"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os.path
import wx

# Editra Libraries
import util
import ed_msg
import syntax.synglob as synglob
import ebmlib

# Local imports
from PyTools.Debugger.RpdbDebugger import RpdbDebugger
from PyTools.Common.PyToolsUtils import PyToolsUtils

# Globals
_ = wx.GetTranslation

ID_ON_RUNTOLINE = wx.NewId()
ID_ON_JUMP = wx.NewId()
#-----------------------------------------------------------------------------#

class MessageHandler(object):
    """Module Message Handler"""
    __metaclass__ = ebmlib.Singleton
    def __init__(self):
        """Initialize"""
        super(MessageHandler, self).__init__()

        # Attributes
        self._prevfile = u""
        self.editor = None
        self.editorlineno = None
        self.contextlineno = None
        self.contextmenus = {1:(True, ID_ON_RUNTOLINE, _("Run To Line"), self.OnRunToLine), 
                             2:(True, ID_ON_JUMP, _("Jump"), self.OnJump)}
        self.debugeditorupdate = lambda x,y,z:None

        # Setup debugger hooks
        rpdbdebugger = RpdbDebugger() # singleton don't keep ref
        rpdbdebugger.conflictingmodules = self.ConflictingModules
        rpdbdebugger.clearstepmarker = self.ClearStepMarker
        rpdbdebugger.setstepmarker = self.SetStepMarker
        rpdbdebugger.restorestepmarker = self.RestoreStepMarker
        
        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)        
        ed_msg.Subscribe(self.OnContextMenu, ed_msg.EDMSG_UI_STC_CONTEXT_MENU)

    # Properties
    ContextLine = property(lambda self: self.contextlineno,
                           lambda self, line: setattr(self, 'contextlineno', line))
    PreviousFile = property(lambda self: self._prevfile,
                            lambda self, fname: setattr(self, '_prevfile', fname))

    @property
    def mainwindow(self):
        mw = wx.GetApp().GetActiveWindow() # Gets main window if one created
        return mw

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
        self.editor = PyToolsUtils.GetEditorOrOpenFile(self.mainwindow, fileName)
        self.editorlineno = lineNo - 1
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    def RestoreStepMarker(self, editor):
        if not editor or self.editor != editor:
            return
        self.editor.GotoLine(self.editorlineno)
        self.editor.ShowStepMarker(self.editorlineno, show=True)
        
    def UpdateForEditor(self, editor, force=False):
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        filename = os.path.normcase(editor.GetFileName())
        self.debugeditorupdate(ispython, filename, force)
        self._prevfile = filename
        RpdbDebugger().saveandrestoreexpressions()
        RpdbDebugger().saveandrestorebreakpoints()
        self.RestoreStepMarker(editor)

    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        self.UpdateForEditor(editor)

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = PyToolsUtils.GetEditorForFile(self.mainwindow, msg.GetData())
        self.UpdateForEditor(editor)

    def OnFileSave(self, msg):
        """Load File message"""
        filename, tmp = msg.GetData()
        editor = PyToolsUtils.GetEditorForFile(self.mainwindow, filename)
        self.UpdateForEditor(editor)

    def AddMenuItem(self, pos, reqattach, wxid, menutitle, menufncallback):
        self.contextmenus[pos] = (reqattach, wxid, menutitle, menufncallback)
    
    def DeleteMenuItem(self, pos):
        del self.contextmenus[pos]
    
    def OnContextMenu(self, msg):
        """Customize the editor buffers context menu"""
        if not len(self.contextmenus):
            return
        ctxmgr = msg.GetData()
        editor = ctxmgr.GetUserData('buffer')
        if not editor:
            return
        langid = editor.GetLangId()
        if langid != synglob.ID_LANG_PYTHON:
            return

        # Add our custom options to the menu
        menu = ctxmgr.GetMenu()
        self.contextlineno = editor.LineFromPosition(ctxmgr.GetPosition()) + 1
        menu.AppendSeparator()
        for pos in sorted(self.contextmenus.keys()):
            reqattach, wxid, menutitle, menufncallback = self.contextmenus[pos]
            if reqattach and not RpdbDebugger().attached:
                continue
            menu.Append(wxid, menutitle)
            ctxmgr.AddHandler(wxid, menufncallback)

    def OnRunToLine(self, editor, event):
        RpdbDebugger().run_toline(editor.GetFileName(), self.contextlineno)

    def OnJump(self, editor, event):
        RpdbDebugger().do_jump(self.contextlineno)
