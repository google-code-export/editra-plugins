# -*- coding: utf-8 -*-
###############################################################################
# Name: __init__.py                                                           #
# Purpose: PyRun Plugin                                                       #
# Author: Fred Lionetti <flionetti@gmail.com>
#         based closely on Cody Precord's PyShell                             #
# Copyright: (c) 2007 Fred Lionetti <flionetti@gmail.com>                     #
# Licence: wxWindows Licence                                                  #
###############################################################################
# Plugin Metadata
"""Executes python script in the Shelf"""
__author__ = "Fred Lionetti"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import os
import wx
import threading
from subprocess import Popen, PIPE, STDOUT

# Editra imports
import iface
import plugin
import util

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Interface Implementation
class PyRun(plugin.Plugin):
    """Adds a PyRun to the Shelf"""
    plugin.Implements(iface.ShelfI)
    ID_PYRUN = wx.NewId()
    __name__ = u'PyRun'

    def AllowMultiple(self):
        """PyRun allows multiple instances"""
        return True

    def CreateItem(self, parent):
        """Returns a PyRun Panel"""
        self._log = wx.GetApp().GetLog()
        self._log("[PyRun][info] Creating PyRun instance for Shelf")

        output = OutputWindow(parent)
        window = wx.GetApp().GetTopWindow()
        if getattr(window, '__name__', ' ') == 'MainWindow':
            fname = window.GetNotebook().GetCurrentCtrl().GetFileName()
            worker = threading.Thread(target=RunCmd, args=[output, fname])
            worker.start()
            wx.CallLater(100, output.Start, 150)
        return output

    def GetId(self):
        return self.ID_PYRUN

    def GetMenuEntry(self, menu):
        return wx.MenuItem(menu, self.ID_PYRUN, self.__name__, 
                                        _("Executes python script"))

    def GetName(self):
        return self.__name__

#-----------------------------------------------------------------------------#
edEVT_UPDATE_TEXT = wx.NewEventType()
EVT_UPDATE_TEXT = wx.PyEventBinder(edEVT_UPDATE_TEXT, 1)
class UpdateTextEvent(wx.PyCommandEvent):
    """Event for passing update messages and signaling the
    output window that there are messages to process.

    """
    def __init__(self, etype, eid, value=''):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value

#-----------------------------------------------------------------------------#

class OutputWindow(wx.TextCtrl):
    """Output buffer to display results of running a script"""
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE)

        # Attributes
        self._updates = list()
        self._timer = wx.Timer(self)

        # Event Handlers
        self.Bind(EVT_UPDATE_TEXT, self.OnUpdate)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __del__(self):
        """Ensure timer is cleaned up when we are deleted"""
        util.Log("[PyRun][info] Stopping timer for %d" % self.GetId())
        if self._timer.IsRunning():
            self._timer.Stop()

    def OnTimer(self, evt):
        """Process and display text from the update buffer"""
        out = self._updates[:]
        if len(out):
            self.AppendText(''.join(out))
            self.SetInsertionPoint(self.GetLastPosition())
            self.Refresh()
            self.Update()
            self._updates = self._updates[len(out):]
        else:
            pass

    def OnUpdate(self, evt):
        """Buffer output before adding to window"""
        self._updates.append(evt.GetValue())
        
    def Start(self, interval):
        """Start the window's timer to check for updates
        @param interval: interval in milliseconds to do updates

        """
        self._timer.Start(interval)

#-----------------------------------------------------------------------------#

def RunCmd(outwin, filename, execcmd="python -u"):
    if filename == "":
        return ""

    filedir = os.path.dirname(filename)
    command = "%s %s" % (execcmd, filename)
    proc_env = dict()
    proc_env['PATH'] = os.environ.get('PATH', '.')
    
    p = Popen(command, shell=True, stdout=PIPE, 
              stderr=STDOUT, cwd=filedir, env=proc_env)

    evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, "> %s" % command + os.linesep)
    wx.CallAfter(wx.PostEvent, outwin, evt)

    while True:
       result = p.stdout.readline()
       if result == "" or result == None: break
       evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, result)
       wx.CallAfter(wx.PostEvent, outwin, evt)

    evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, "> Exit code: %d%s" % (p.wait(), os.linesep))
    wx.CallAfter(wx.PostEvent, outwin, evt)
    return outwin.GetValue()

