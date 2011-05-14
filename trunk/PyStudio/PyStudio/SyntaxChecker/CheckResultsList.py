# -*- coding: utf-8 -*-
# Name: CheckResultsList.py
# Purpose: Pylint plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
###############################################################################

"""Editra Shelf display window"""

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libraries
import ed_msg
import ed_marker
import eclib

# Local imports
from PyStudio.Common.PyStudioUtils import PyStudioUtils

# Globals
_ = wx.GetTranslation

#----------------------------------------------------------------------------#

class CheckResultsList(eclib.EBaseListCtrl):
    """List control for displaying syntax check results
    @todo: decouple marks and data from UI

    """
    _cache = dict()
    def __init__(self, parent):
        super(CheckResultsList, self).__init__(parent)

        # Attributes
        self.editor = None
        self._mw = None

        # Setup
        self.InsertColumn(0, _("Type"))
        self.InsertColumn(1, _("Line"))
        self.InsertColumn(2, _("Error"))
        self.SetColumnWidth(1, wx.LIST_AUTOSIZE_USEHEADER)

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivate)

        # Message Handler
        ed_msg.Subscribe(self.OnDwellStart, ed_msg.EDMSG_UI_STC_DWELL_START)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    def OnDestroy(self, evt):
        if evt.GetEventObject() is self:
            ed_msg.Unsubscribe(self.OnDwellStart)
            self.ClearMarkers()

    def set_mainwindow(self, mw):
        self._mw = mw

    def set_editor(self, editor):
        self.editor = editor

    def OnDwellStart(self, msg):
        """Show calltips for the error if dwelling over a line"""
        data = msg.GetData()
        buf = data.get('stc', None)
        if buf:
            lineno = data.get('line', -1)
            fname = buf.GetFileName()
            if fname in CheckResultsList._cache:
                errorlist = CheckResultsList._cache[fname].GetLineData(lineno)
                if errorlist and len(errorlist):
                    errors = [ "%s %s" % err for err in errorlist ]
                    data['rdata'] = "\n".join(errors)

    def OnItemActivate(self, evt):
        """Go to the error in the file"""
        if self.editor:
            idx = evt.GetIndex()
            itm = self.GetItem(idx, 1).GetText()
            try:
                lineNo = int(itm)
                self.editor.GotoLine(max(0, lineNo - 1))
            except ValueError:
                pass

    @staticmethod
    def DeleteEditorMarkers(editor):
        """Remove lint markers from the given editor"""
        editor.RemoveAllMarkers(ed_marker.LintMarker())
        editor.RemoveAllMarkers(ed_marker.LintMarkerError())
        editor.RemoveAllMarkers(ed_marker.LintMarkerWarning())

    def Clear(self):
        """Delete all the rows """
        if self.editor:
            fname = self.editor.GetFileName()
            if fname in CheckResultsList._cache:
                del CheckResultsList._cache[fname]
            self.DeleteAllItems()
            self.DeleteEditorMarkers(self.editor)

    def ClearMarkers(self):
        """Clear markers from all buffers"""
        if self._mw:
            nb = self._mw.GetNotebook()
            if nb:
                ctrls = nb.GetTextControls()
                for ctrl in ctrls:
                    if ctrl and ctrl.GetFileName() in CheckResultsList._cache:
                        self.DeleteEditorMarkers(ctrl)

    def GetCachedData(self):
        """Get the cached Lint data for the current editor
        @return: tuple(filename, LintData)

        """
        if self.editor:
            fname = self.editor.GetFileName()
            data = CheckResultsList._cache.get(fname, None)
        else:
            fname = u""
            data = None
        return fname, data

    def LoadData(self, data, fname=None):
        """Load data into the cache and display it in the list
        @param fname: filename
        @param data: Lint data [(errorType, errorText, errorLine),]

        """
        if fname is None:
            if not self.editor:
                return # TODO: Log
            fname = self.editor.GetFileName()
        else:
            self.editor = PyStudioUtils.GetEditorOrOpenFile(self._mw, fname)
        CheckResultsList._cache[fname] = LintData(data)
        self._PopulateRows(CheckResultsList._cache[fname])

    def _PopulateRows(self, data):
        """Populate the list with the data
        @param data: LintData object

        """
        typeText = _("Type")
        errorText = _("Error")
        minLType = max(self.GetTextExtent(typeText)[0], self.GetColumnWidth(0))
        minLText = max(self.GetTextExtent(errorText)[0], self.GetColumnWidth(2))
        for row in data.GetOrderedData():
            assert len(row) == 3
            mtype = row[0]
            dspmsg = LintData.GetDisplayString(mtype)
            minLType = max(minLType, self.GetTextExtent(dspmsg)[0])
            minLText = max(minLText, self.GetTextExtent(row[2])[0])
            row[0] = dspmsg
            self.Append(row)
            if self.editor:
                try:
                    if mtype == 'Error':
                        mark = ed_marker.LintMarkerError()
                    elif mtype == 'Warning':
                        mark = ed_marker.LintMarkerWarning()
                    else:
                        mark = ed_marker.LintMarker()
                    self.editor.AddMarker(mark,
                                          int(row[1]) - 1) # TODO: store handles
                except ValueError:
                    pass
        self.SetColumnWidth(0, minLType)
        self.SetColumnWidth(2, minLText)

#-----------------------------------------------------------------------------#

class LintData(object):
    """PyLint output data management object"""
    def __init__(self, data):
        """@param data: [(type, text, line),]"""
        super(LintData, self).__init__()

        # Attributes
        self._data = dict() # lineno -> [(errorType, errorText),]

        # Setup
        for val in data:
            assert len(val) == 3
            line = val[2]
            if line not in self._data:
                self._data[line] = list()
            self._data[line].append((unicode(val[0]), unicode(val[1]).rstrip()))

    Data = property(lambda self: self._data)

    def GetOrderedData(self):
        """Iterate over the data ordered by line number
        @return: [(errType, line, errText),]

        """
        rdata = list()
        for key in sorted(self._data.keys()):
            for data in self._data[key]:
                if isinstance(key, basestring):
                    rdata.insert(0, [data[0], unicode(key), data[1]])
                else:
                    rdata.append([data[0], unicode(key), data[1]])
        return rdata

    def GetLineData(self, line):
        """Get data for the given line
        @param line: line number (int)
        @return: [(errType, errText),] or None

        """
        return self._data.get(line, None)

    @staticmethod
    def GetDisplayString(mtype):
        """Get the display string for the given mesage type"""
        msgmap = { 'Error' : _("Error"),
                   'Warning' : _("Warning"),
                   'Convention' : _("Convention"),
                   'Refactor' : _("Refactor") }
        return msgmap.get(mtype, _("Warning"))
