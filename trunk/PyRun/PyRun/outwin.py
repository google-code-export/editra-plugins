###############################################################################
# Name: outwin.py                                                             #
# Purpose: Result output window and related controls                          #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import wx
import threading
from subprocess import Popen, PIPE, STDOUT

# Editra Imports
import util
from profiler import Profile_Get, Profile_Set

# Function Aliases
_ = wx.GetTranslation

# Globals
PYRUN_EXE = 'PyRun.PyExe'   # Profile key for saving prefered python command

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

edEVT_PROCESS_START = wx.NewEventType()
EVT_PROCESS_START = wx.PyEventBinder(edEVT_PROCESS_START, 1)
class ProcessStartEvent(UpdateTextEvent):
    """Message that process should be started"""
    pass

edEVT_PROCESS_EXIT = wx.NewEventType()
EVT_PROCESS_EXIT = wx.PyEventBinder(edEVT_PROCESS_EXIT, 1)
class ProcessExitEvent(wx.PyCommandEvent):
    """Event for notifying that the script has finished executing"""
    pass

#-----------------------------------------------------------------------------#

class OutputWindow(wx.Panel):
    """Output window that contains the configuration controls and
    output buffer for the running instance of PyRun. This is the main
    ui component returned by the plugin object.

    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # Attributes
        self._log = wx.GetApp().GetLog()
        self._ctrl = ConfigBar(self)
        self._buffer = OutputBuffer(self)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(EVT_PROCESS_START, self.OnRunScript)
        self.Bind(EVT_PROCESS_EXIT, self.OnEndScript)

    def __DoLayout(self):
        """Layout/Create the windows controls"""
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)

        vsizer.AddMany([(self._ctrl, 0, wx.EXPAND), 
                        (self._buffer, 1, wx.EXPAND)])
        msizer.Add(vsizer, 1, wx.EXPAND)
        self.SetSizer(msizer)
        self.SetAutoLayout(True)

    def _DoRunCmd(self, filename, execmd="python"):
        """This is a worker function that runs a python script on
        on a separate thread and posts the output back to the output
        buffer this requires that all interaction with the gui be
        done by posting events as apposed to accessing items directly.
        @param filename: full path to script to run
        @keyword execmd: python to execute script with

        """
        if filename == "":
            return ""

        filedir = os.path.dirname(filename)
        command = "%s %s" % (execmd, filename)
        proc_env = dict()
        proc_env['PATH'] = os.environ.get('PATH', '.')
        proc_env['PYTHONUNBUFFERED'] = '1'
        
        p = Popen(command, shell=True, stdout=PIPE, 
                  stderr=STDOUT, cwd=filedir, env=proc_env)

        evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, "> %s" % command + os.linesep)
        wx.CallAfter(wx.PostEvent, self._buffer, evt)

        while True:
           result = p.stdout.readline()
           if result == "" or result == None: break
           evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, result)
           wx.CallAfter(wx.PostEvent, self._buffer, evt)

        evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, "> Exit code: %d%s" % (p.wait(), os.linesep))
        wx.CallAfter(wx.PostEvent, self._buffer, evt)

        # Notify that proccess has exited
        evt = ProcessExitEvent(edEVT_PROCESS_EXIT, -1)
        wx.CallAfter(wx.PostEvent, self, evt)

    def OnEndScript(self, evt):
        """Handle when the process exits"""
        self._log("[PyRun][info] Script has finished")
        self._buffer.Stop()
        self._ctrl.Enable()

    def OnRunScript(self, evt):
        """Handle events posted by control bar to re-run the script"""
        self._log("[PyRun][info] Starting Script: %s..." % script)
        script = evt.GetValue()
        self.RunScript(script)

    def RunScript(self, fname):
        """Start the worker thread that runs the python script"""
        self._buffer.Clear()
        self._ctrl.Disable()
        self._ctrl.SetCurrentFile(fname)
        pyexe = self._ctrl.GetPythonCommand()
        worker = threading.Thread(target=self._DoRunCmd, args=[fname, pyexe])
        worker.start()
        self.Layout()
        wx.CallLater(150, self._buffer.Start, 150)

#-----------------------------------------------------------------------------#

class OutputBuffer(wx.TextCtrl):
    """Output buffer to display results of running a script"""
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE)

        # Attributes
        self._log = wx.GetApp().GetLog()
        self._updates = list()
        self._timer = wx.Timer(self)

        # Setup
        font = self.GetFont()
        if wx.Platform == '__WXMAC__':
            font.SetPointSize(12)
            self.MacCheckSpelling(False)
        else:
            font.SetPointSize(10)
        self.SetFont(font)

        # Event Handlers
        self.Bind(EVT_UPDATE_TEXT, self.OnUpdate)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

    def __del__(self):
        """Ensure timer is cleaned up when we are deleted"""
        self._log("[PyRun][info] Stopping timer for %d" % self.GetId())
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
        self._log("[PyRun][info] Starting output to buffer on timer")
        self._timer.Start(interval)

    def Stop(self):
        """Stop the update process of the buffer"""
        self._log("[PyRun][info] Process Finished, stopping timer")

        # Dump any output still left in tmp buffer before stopping
        self.OnTimer(None)
        self._timer.Stop()

#-----------------------------------------------------------------------------#

class ConfigBar(wx.Panel):
    """Small configuration bar for showing what python is being
    used to run the script, as well as allowing it to be changed,
    and allows for re-running the script.

    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(-1, 24))

        # Attributes
        pyexe = Profile_Get(PYRUN_EXE, 'str', 'python')
        if not len(pyexe):
            pyexe = 'python'
        self._pbuff = wx.TextCtrl(self, value=pyexe)
        self._pbuff.SetMinSize((150, -1))
        self._pbuff.SetMaxSize((-1, 20))
        self._fname = ''                                # Current File
        self._cfile = wx.StaticText(self, label='')     # Current File Display
        self._run = wx.Button(self, label=_("Run Script"))
        if wx.Platform == '__WXMAC__':
            self._run.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, self._run)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def __DoLayout(self):
        """Layout the controls in the bar"""
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl = wx.StaticText(self, label=_("Python Executable") + u':')

        if wx.Platform == '__WXMAC__':
            lbl.SetFont(wx.SMALL_FONT)
            self._cfile.SetFont(wx.SMALL_FONT)

        hsizer.AddMany([((20, 24)), (lbl, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5)), (self._pbuff, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((20, 15)), (self._cfile, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5), 1, wx.EXPAND), (self._run, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                        ((8, 8))])
        self.SetSizer(hsizer)
        self.SetAutoLayout(True)

    def GetCurrentFile(self):
        """Get the current file that is shown in the display
        @return: string

        """
        return self._fname

    def GetPythonCommand(self):
        """Get the command that is set in the text control or
        the default value if nothing is set.
        @return: python command string

        """
        cmd = self._pbuff.GetValue().strip()
        if not len(cmd):
            return Profile_Get(PYRUN_EXE, 'str', 'python')
        else:
            return cmd

    def OnButton(self, evt):
        """Post an event to request the script be run again"""
        sevt = ProcessStartEvent(edEVT_PROCESS_START, self.GetId(), self._fname)
        wx.PostEvent(self.GetParent(), sevt)

    def OnPaint(self, evt):
        """Paints the background of the bar with a nice gradient.
        @param evt: Event that called this handler
        @type evt: wx.PaintEvent

        """
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        col1 = wx.SystemSettings_GetColour(wx.SYS_COLOUR_3DFACE)
        col2 = util.AdjustColour(col1, 50)
        col1 = util.AdjustColour(col1, -60)
        grad = gc.CreateLinearGradientBrush(0, 1, 0, 24, col2, col1)
        rect = self.GetClientRect()

        pen_col = tuple([min(190, x) for x in util.AdjustColour(col1, -60)])
        gc.SetPen(gc.CreatePen(wx.Pen(pen_col, 1)))
        gc.SetBrush(grad)
        gc.DrawRectangle(0, 1, rect.width - 0.5, rect.height - 0.5)

        evt.Skip()

    def SetCurrentFile(self, fname):
        """Set the name of the current file for the display"""
        self._fname = fname
        script = os.path.split(fname)[1]
        self._cfile.SetLabel(_("Current Script: %s") % script)
        self.GetParent().Layout()
        self.Layout()
        
#-----------------------------------------------------------------------------#
