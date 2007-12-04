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
import sys
import re
import wx
import threading
import signal
from subprocess import Popen, PIPE, STDOUT

# Needed for killing processes on windows
if sys.platform.startswith('win'):
    import ctypes

# Editra Imports
import util
from profiler import Profile_Get, Profile_Set

#pre build error regular expression
error_re = re.compile('.*File "(.+)", line ([0-9]+)')
info_re = re.compile('[>]{3,3}.*' + os.linesep)

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

edEVT_PROCESS_ABORT = wx.NewEventType()
EVT_PROCESS_ABORT = wx.PyEventBinder(edEVT_PROCESS_ABORT, 1)
class ProcessAbortEvent(wx.PyCommandEvent):
    """Event for notifying that the script should be aborted"""
    pass

edEVT_PROCESS_CLEAR = wx.NewEventType()
EVT_PROCESS_CLEAR = wx.PyEventBinder(edEVT_PROCESS_CLEAR, 1)
class ProcessClearEvent(wx.PyCommandEvent):
    """Event for clearing output window"""
    pass

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
        self._worker = None
        self._abort = False                 # Flag to abort script

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(EVT_PROCESS_ABORT, self.OnAbortScript)
        self.Bind(EVT_PROCESS_CLEAR, self.OnClear)
        self.Bind(EVT_PROCESS_START, self.OnRunScript)
        self.Bind(EVT_PROCESS_EXIT, self.OnEndScript)

    def __del__(self):
        """Cleanup any running processes on exit"""
        self._log("[PyRun][info] Output window deleted: %d" % self.GetId())
        self._abort = True

    def __DoLayout(self):
        """Layout/Create the windows controls"""
        msizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.AddMany([(self._ctrl, 0, wx.EXPAND, 2), 
                        (self._buffer, 1, wx.EXPAND)])
        msizer.Add(vsizer, 1, wx.EXPAND)
        self.SetSizer(msizer)
        self.SetAutoLayout(True)

    def __DoOneRead(self, proc):
        """Read one line of output and post results. Returns True
        if there is more to read and False if there is not. This is
        a private function called by the worker thread to retrieve
        output.

        """
        result = proc.stdout.readline()
        if result == "" or result == None:
            return False
        evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, result)
        wx.CallAfter(wx.PostEvent, self._buffer, evt)
        return True

    def __KillPid(self, pid):
        """Kill a process by process id"""
        if wx.Platform in ['__WXMAC__', '__WXGTK__']:
            os.kill(pid, signal.SIGABRT)
            os.waitpid(pid, os.WNOHANG)
        else:
            PROCESS_TERMINATE = 1
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)

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

        filedir, filename = os.path.split(filename)
        filename = '"%s"' % filename
        command = "%s %s" % (execmd, filename)
        proc_env = self._PrepEnv()
        
        p = Popen(command, stdout=PIPE, stderr=STDOUT, 
                  shell=True, cwd=filedir, env=proc_env)

        evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, ">>> %s" % command + os.linesep)
        wx.CallAfter(wx.PostEvent, self._buffer, evt)


        # Read from stdout while there is output from process
        while True:
            if self._abort:
                self.__KillPid(p.pid)
                self.__DoOneRead(p)
                break
            else:
                try:
                    more = self.__DoOneRead(p)
                except wx.PyDeadObjectError:
                    # We are dead so kill process and return
                    self.__KillPid(p.pid)
                    return
                else:
                    if not more:
                        break

        evt = UpdateTextEvent(edEVT_UPDATE_TEXT, -1, ">>> Exit code: %d%s" % (p.wait(), os.linesep))
        wx.CallAfter(wx.PostEvent, self._buffer, evt)

        # Notify that proccess has exited
        evt = ProcessExitEvent(edEVT_PROCESS_EXIT, -1)
        wx.CallAfter(wx.PostEvent, self, evt)

    def _PrepEnv(self):
        """Create an environment for the process to run in"""
        if not hasattr(sys, 'frozen') or wx.Platform == '__WXMSW__':
            proc_env = os.environ.copy()
        else:
            proc_env = dict()

        proc_env['PYTHONUNBUFFERED'] = '1'
        return proc_env

    def Abort(self):
        """Abort the current process if one is running"""
        if self._worker is None:
            return

        # Flag desire to abort for worker thread to notice
        self._abort = True

        # Wait for it to die
        self._worker.join(1)
        if self._worker.isAlive():
            self._log("[PyRun][info] Forcing thread to stop")
            self._worker._Thread__stop()
        self._worker = None

        self._buffer.Stop()
        self._ctrl.Enable()

    def Clear(self):
        """Clears the contents of the buffer"""
        self._buffer.Clear()
 
    def OnClear(self, evt):
        """Handle request to clear output window"""
        self._log("[PyRun][info] Clearing output...")
        self.Clear()

    def OnAbortScript(self, evt):
        """Handle request to abort the current running script"""
        self._log("[PyRun][info] Aborting current script...")
        self.Abort()

    def OnEndScript(self, evt):
        """Handle when the process exits"""
        self._log("[PyRun][info] Script has finished")
        self._buffer.Stop()
        self._ctrl.Enable()

    def OnRunScript(self, evt):
        """Handle events posted by control bar to re-run the script"""
        script = evt.GetValue()
        self._log("[PyRun][info] Starting Script: %s..." % script)
        self.RunScript(script)

    def RunScript(self, fname):
        """Start the worker thread that runs the python script"""
        self._abort = False
        self._buffer.SetValue('')
        self._ctrl.Disable()
        self._ctrl.SetCurrentFile(fname)
        pyexe = self._ctrl.GetPythonCommand()
        if len(pyexe):
            Profile_Set(PYRUN_EXE, pyexe)
        self._log("[PyRun][info] Running script with command: %s" % pyexe)
        self._worker = threading.Thread(target=self._DoRunCmd, args=[fname, pyexe])
        self._worker.start()
        self.Layout()
        wx.CallLater(150, self._buffer.Start, 175)

#-----------------------------------------------------------------------------#

class OutputBuffer(wx.TextCtrl):
    """Output buffer to display results of running a script"""
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2)

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
        if self._timer.IsRunning():
            self._log("[PyRun][info] Stopping timer for %d" % self.GetId())
            self._timer.Stop()

    def ApplyStyles(self, start, txt):
        """Apply coloring to text starting at start position
        @param start: start position in buffer
        @param txt: text to locate styling point in

        """
        for group in error_re.finditer(txt):
            self.SetStyle(start + group.start(), start + group.end(), 
                          wx.TextAttr("RED", wx.NullColour))
        else:
            for info in info_re.finditer(txt):
                end = start + info.end()
                self.SetStyle(start + info.start(), end,
                              wx.TextAttr("BLUE", wx.NullColour))

                self.SetStyle(end, end, wx.TextAttr("BLACK", wx.NullColour))

    def OnTimer(self, evt):
        """Process and display text from the update buffer
        @note: this gets called many times while running thus needs to
               return quickly to avoid blocking the ui.

        """
        out = self._updates[:]
        if len(out):
            txt = ''.join(out)
            start = self.GetInsertionPoint()
            self.AppendText(txt)
            self.SetInsertionPoint(self.GetLastPosition())
            self.Refresh()
            self.Update()
            self._updates = self._updates[len(out):]
            wx.CallAfter(self.ApplyStyles, start, txt)
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
ID_RUN_BTN = wx.NewId()
ID_CLEAR_BTN = wx.NewId()
class ConfigBar(wx.Panel):
    """Small configuration bar for showing what python is being
    used to run the script, as well as allowing it to be changed,
    and allows for re-running the script.

    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size=(-1, 28))

        # Attributes
        pyexe = Profile_Get(PYRUN_EXE, 'str', 'python')
        if not len(pyexe):
            pyexe = 'python'
        self._pbuff = wx.TextCtrl(self, value=pyexe)
        self._pbuff.SetMinSize((150, -1))
        self._pbuff.SetMaxSize((-1, 20))
        self._pbuff.SetToolTipString(_("Path to Python executable or name of executable to use"))
        self._fname = ''                                # Current File
        self._cfile = wx.StaticText(self, label='')     # Current File Display
        self._run = wx.Button(self, ID_RUN_BTN, _("Run Script"))
        self._clear = wx.Button(self, ID_CLEAR_BTN, label=_("Clear"))
        if wx.Platform == '__WXMAC__':
            self._pbuff.SetFont(wx.SMALL_FONT)
            self._pbuff.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
            self._run.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
            self._clear.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=ID_RUN_BTN)
        self.Bind(wx.EVT_BUTTON, self.OnButton, id=ID_CLEAR_BTN)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def __DoLayout(self):
        """Layout the controls in the bar"""
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        lbl = wx.StaticText(self, label=_("Python Executable") + u':')

        if wx.Platform == '__WXMAC__':
            lbl.SetFont(wx.SMALL_FONT)
            self._cfile.SetFont(wx.SMALL_FONT)

        hsizer.AddMany([((20, 28)), (lbl, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5)), (self._pbuff, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((20, 15)), (self._cfile, 0, wx.ALIGN_CENTER_VERTICAL),
                        ((5, 5), 1, wx.EXPAND), (self._run, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                        ((5,5)), (self._clear, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL),
                        ((8, 8))])
        self.SetSizer(hsizer)
        self.SetAutoLayout(True)

    def Disable(self):
        """Disable the panel except for the button which is
        changed to an abort button.

        """
        for child in self.GetChildren():
            c_id = child.GetId()
            if c_id == ID_CLEAR_BTN:
                continue
            elif c_id == ID_RUN_BTN:
                child.SetLabel(_("Abort"))
            else:
                child.Disable()

    def Enable(self, enable=True):
        """Enable all items in the bar and change the button back
        to Run Script.

        """
        for child in self.GetChildren():
            if child.GetId() == ID_RUN_BTN:
                child.SetLabel(_("Run Script"))
            else:
                child.Enable(enable)

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
        """Post an event to request the script be run again or aborted"""
        e_id = evt.GetId()
        lbl = evt.GetEventObject().GetLabel()
        if e_id == ID_RUN_BTN:
            if lbl == _("Run Script"):
                sevt = ProcessStartEvent(edEVT_PROCESS_START, 
                                         self.GetId(), self._fname)
            else:
                sevt = ProcessAbortEvent(edEVT_PROCESS_ABORT, self.GetId())
        elif e_id == ID_CLEAR_BTN:
            sevt = ProcessClearEvent(edEVT_PROCESS_CLEAR, self.GetId())
        else:
            evt.Skip()
            return

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
