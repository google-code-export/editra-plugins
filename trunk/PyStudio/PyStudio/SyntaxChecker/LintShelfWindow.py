# -*- coding: utf-8 -*-
# Name: LintShelfWindow.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import wx

# Editra Libraries
import util
import ed_glob
import ed_msg
import syntax.synglob as synglob

# Local imports
from PyStudio.Common import ToolConfig
from PyStudio.Common import Images
from PyStudio.Common.PyStudioUtils import PyStudioUtils
from PyStudio.Common.BaseShelfWindow import BaseShelfWindow
from PyStudio.SyntaxChecker.CheckResultsList import CheckResultsList
from PyStudio.SyntaxChecker.PythonSyntaxChecker import PythonSyntaxChecker
from PyStudio.SyntaxChecker.CAResultsXml import AnalysisResults

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class LintShelfWindow(BaseShelfWindow):
    """Syntax Check Results Window"""
    __syntaxCheckers = {
        synglob.ID_LANG_PYTHON: PythonSyntaxChecker
    }

    def __init__(self, parent):
        """Initialize the window"""
        super(LintShelfWindow, self).__init__(parent)

        ctrlbar = self.setup(CheckResultsList(self))
        ctrlbar.AddControl(wx.StaticLine(ctrlbar, size=(-1, 16), style=wx.LI_VERTICAL),
                           wx.ALIGN_LEFT)
        self.savebtn = self.AddPlateButton(u"", ed_glob.ID_SAVE, wx.ALIGN_LEFT)
        self.savebtn.ToolTip = wx.ToolTip(_("Save Results"))
        self.openbtn = self.AddPlateButton(u"", ed_glob.ID_OPEN, wx.ALIGN_LEFT)
        self.openbtn.ToolTip = wx.ToolTip(_("Load Results"))
        self._lbl = wx.StaticText(ctrlbar)
        ctrlbar.AddControl(self._lbl)
        ctrlbar.AddStretchSpacer()
        self.layout("Analyze", self.OnRunLint, self.OnJobTimer)
        self.TaskButton.SetBitmap(Images.Lint.Bitmap)
        self.clearbtn = self.AddPlateButton(_("Clear"), ed_glob.ID_DELETE, wx.ALIGN_RIGHT)

        # Attributes
        self._checker = None

        # Editra Message Handlers
        ed_msg.Subscribe(self.OnFileLoad, ed_msg.EDMSG_FILE_OPENED)
        ed_msg.Subscribe(self.OnFileSave, ed_msg.EDMSG_FILE_SAVED)
        ed_msg.Subscribe(self.OnPageChanged, ed_msg.EDMSG_UI_NB_CHANGED)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnSaveResults, self.savebtn)
        self.Bind(wx.EVT_BUTTON, self.OnOpenResults, self.openbtn)
        self.Bind(wx.EVT_BUTTON, self.OnClear, self.clearbtn)

    def Unsubscription(self):
        ed_msg.Unsubscribe(self.OnFileLoad)
        ed_msg.Unsubscribe(self.OnFileSave)
        ed_msg.Unsubscribe(self.OnPageChanged)

    def OnThemeChanged(self, msg):
        """Update Icons"""
        super(LintShelfWindow, self).OnThemeChanged(msg)
        for btn, bmp in ((self.savebtn, ed_glob.ID_SAVE),
                         (self.openbtn, ed_glob.ID_OPEN),
                         (self.clearbtn, ed_glob.ID_DELETE)):
            bitmap = wx.ArtProvider.GetBitmap(str(bmp), wx.ART_MENU)
            btn.SetBitmap(bitmap)
            btn.Refresh()

    def _onfileaccess(self, editor):
        if not editor:
            return
        self._listCtrl.set_editor(editor)
        self._listCtrl.Clear()

        # With the text control (ed_stc.EditraStc) this will return the full
        # path of the file or a wx.EmptyString if the buffer does not contain
        # an on disk file
        filename = editor.GetFileName()
        if not filename:
            return
        filename = os.path.abspath(filename)

        filetype = editor.GetLangId()
        directoryvariables = self.get_directory_variables(filetype)
        if directoryvariables:
            vardict = directoryvariables.read_dirvarfile(filename)
        else:
            vardict = {}

        self._checksyntax(filetype, vardict, filename)
        self._hasrun = True

    def UpdateForEditor(self, editor, force=False):
        """Update the ControlBar for the given editor instance"""
        langid = getattr(editor, 'GetLangId', lambda: -1)()
        ispython = langid == synglob.ID_LANG_PYTHON
        self.taskbtn.Enable(ispython)
        if force or not self._hasrun:
            ctrlbar = self.GetControlBar(wx.TOP)
            ctrlbar.Layout()

    def OnClear(self, evt):
        """Clear the results"""
        self._listCtrl.Clear()

    def OnPageChanged(self, msg):
        """ Notebook tab was changed """
        notebook, pg_num = msg.GetData()
        editor = notebook.GetPage(pg_num)
        if ToolConfig.GetConfigValue(ToolConfig.TLC_LINT_AUTORUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnSaveResults(self, evt):
        """Export the results to XML"""
        data = self._listCtrl.GetCachedData()
        if data[1]:
            dlg = wx.FileDialog(self.GetTopLevelParent(),
                                _("Save Results"),
                                wildcard="XML(*.xml)|*.xml",
                                style=wx.FD_SAVE|wx.FD_CHANGE_DIR|wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                outpath = dlg.GetPath()
                if not outpath.endswith('.xml'):
                    outpath += u'.xml'
                results = AnalysisResults()
                results.path = data[0]
                for result in data[1].GetOrderedData():
                    # errType, line, errText
                    results.AddResult(result[1], result[0], result[2])
                if results.Write(outpath):
                    msg = _("Saved PyLint results to: %s") % outpath
                else:
                    msg = _("Failed to save PyLint Results")
                self._mw.PushStatusText(msg, 0)
            dlg.Destroy()
        else:
            self._mw.PushStatusText(_("No data to save!"), 0)

    def OnOpenResults(self, evt):
        """Load the analysis results from xml"""
        dlg = wx.FileDialog(self.GetTopLevelParent(),
                            _("Load Results"),
                            wildcard="XML(*.xml)|*.xml",
                            style=wx.FD_OPEN|wx.FD_CHANGE_DIR)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            results = AnalysisResults.Load(path)
            if results:
                data = list()
                for result in results.results:
                    data.append((result.errType, result.errMsg, result.line))
                self._lbl.Label = results.path
                self._listCtrl.LoadData(data, fname=results.path)
                self._listCtrl.RefreshRows()
                self._mw.PushStatusText(_("Loaded code analysis data: %s") % path, 0)
            else:
                self._mw.PushStatusText(_("Failed to load results data: %s") % path, 0)
        dlg.Destroy()

    def OnFileLoad(self, msg):
        """Load File message"""
        editor = PyStudioUtils.GetEditorForFile(self._mw, msg.GetData())
        if ToolConfig.GetConfigValue(ToolConfig.TLC_LINT_AUTORUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnFileSave(self, msg):
        """Load File message"""
        filename, tmp = msg.GetData()
        editor = PyStudioUtils.GetEditorForFile(self._mw, filename)
        if ToolConfig.GetConfigValue(ToolConfig.TLC_LINT_AUTORUN):
            wx.CallAfter(self._onfileaccess, editor)
            self.UpdateForEditor(editor, True)
        else:
            self.UpdateForEditor(editor)

    def OnRunLint(self, event):
        """Run PyLint Code Analysis on the current buffer"""
        editor = wx.GetApp().GetCurrentBuffer()
        if editor:
            self.taskbtn.Enable(False)
            wx.CallAfter(self._onfileaccess, editor)

    def get_syntax_checker(self, filetype, vardict, filename):
        try:
            return self.__syntaxCheckers[filetype](vardict, filename)
        except Exception:
            pass
        return None

    def _checksyntax(self, filetype, vardict, filename):
        """Start the syntax checker job"""
        syntaxchecker = self.get_syntax_checker(filetype, vardict, filename)
        if not syntaxchecker:
            return
        self._checker = syntaxchecker
        self._curfile = filename

        # Start job timer
        self._StopTimer()
        self._jobtimer.Start(250, True)

    def _OnSyntaxData(self, data):
        # Data is something like
        # [('Syntax Error', '__all__ = ["CSVSMonitorThread"]', 7)]
        self.taskbtn.Enable(True)
        if len(data) != 0:
            self._listCtrl.LoadData(data)
            self._listCtrl.RefreshRows()
        mwid = self.GetMainWindow().GetId()
        ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, False))

    def OnJobTimer(self, evt):
        """Start a syntax check job"""
        if self._checker:
            util.Log("[PyLint][info] fileName %s" % (self._curfile))
            mwid = self.GetMainWindow().GetId()
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_SHOW, (mwid, True))
            ed_msg.PostMessage(ed_msg.EDMSG_PROGRESS_STATE, (mwid, -1, -1))
            # Update the label to show what file the results are for
            self._lbl.SetLabel(self._curfile)
            self._checker.Check(self._OnSyntaxData)
