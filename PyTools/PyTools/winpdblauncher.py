import os
import sys
import ConfigParser
from optparse import OptionParser
import subprocess
import rpdb2
from winpdb import *

if 'wx' not in sys.modules and 'wxPython' not in sys.modules:
    try:
        import wxversion
        wxversion.ensureMinimal(WXVER)
    except ImportError:
        rpdb2._print(STR_WXPYTHON_ERROR_MSG, sys.__stderr__)

        try:
            import Tkinter
            import tkMessageBox

            Tkinter.Tk().wm_withdraw()
            tkMessageBox.showerror(STR_WXPYTHON_ERROR_TITLE, STR_WXPYTHON_ERROR_MSG)

        except:
            pass

        sys.exit(1)
import wx

assert wx.VERSION_STRING >= WXVER

if rpdb2.get_version() != "RPDB_2_4_8":
    rpdb2._print(STR_ERROR_INTERFACE_COMPATIBILITY % ("RPDB_2_4_8", rpdb2.get_version()))
    sys.exit(1)

class WinpdbLauncher(object):
    def __init__(self, remoldbps, args):
        self.remoldbps = remoldbps.upper() == "Y"
        self.args = args
        self.pwd = "123"
        self.sessionmanager = None
        self.winpdbapp = None
        self.breakpoints_set = False
        self.breakpoints = {}

    def callback_events(self, event):
        if not self.sessionmanager or not self.winpdbapp:
            return
        if event.m_state == rpdb2.STATE_DETACHED:
            self.winpdbapp.m_frame.Close()
        elif not self.breakpoints_set and event.m_state == rpdb2.STATE_BROKEN:
            wx.CallAfter(self.callafter_setbreakpoints, event)

    def callafter_setbreakpoints(self, event):
        try:
            self.sessionmanager.load_breakpoints()
            if self.remoldbps:
                rpdb2._print("Removing old breakpoints")
                self.sessionmanager.delete_breakpoint([], True)
        except IOError:
            rpdb2._print("Failed to load old breakpoints")
        rpdb2._print("Setting breakpoints: (Path, Line No, Enabled)")
        for filepath in self.breakpoints:
            linenos = self.breakpoints[filepath]
            for lineno in linenos:
                enabled = linenos[lineno]
                self.sessionmanager.set_breakpoint(filepath, '', lineno, enabled, '')
                rpdb2._print("%s, %d, %s" % (filepath, lineno, enabled))
        self.breakpoints_set = True

    def start_winpdbclient(self):
        fAllowUnencrypted = True
        fRemote = False
        host = "localhost"
        fAttach = True
        fchdir = False
        command_line = self.args[0]

        self.sessionmanager = rpdb2.CSessionManager(self.pwd, fAllowUnencrypted, fRemote, host)

        try:
            self.winpdbapp = CWinpdbApp(self.sessionmanager, fchdir, command_line, fAttach, fAllowUnencrypted)
        except SystemError:
            if os.name == rpdb2.POSIX:
                rpdb2._print(STR_X_ERROR_MSG, sys.__stderr__)
                sys.exit(1)

            raise

        if not 'unicode' in wx.PlatformInfo:
            dlg = wx.MessageDialog(None, STR_WXPYTHON_ANSI_WARNING_MSG, STR_WXPYTHON_ANSI_WARNING_TITLE, wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        event_type_dict = {rpdb2.CEventState: {}}
        self.sessionmanager.register_callback(self.callback_events, \
            event_type_dict, fSingleUse = False)
        self.winpdbapp.MainLoop()
        self.sessionmanager.shutdown()

    def run(self, bpfile):
        config = ConfigParser.ConfigParser()
        config.read(os.path.abspath(bpfile))
        files_to_breakpoint = config.sections()
        for file_to_breakpoint in files_to_breakpoint:
            self.breakpoints[file_to_breakpoint] = {}
            for linenostr in config.options(file_to_breakpoint):
                lineno = int(linenostr)
                enabled = "True" == config.get(file_to_breakpoint, linenostr)
                self.breakpoints[file_to_breakpoint][lineno] = enabled
        callrpdb2 = ["rpdb2", "-d", "--pwd=%s" % self.pwd] + self.args
        rpdb2._print("Breakpoints file read. Running: %s" % " ".join(callrpdb2))
        process = subprocess.Popen(callrpdb2, shell=True)
        self.start_winpdbclient()
        try:
            process.terminate()
        except:
            pass

if __name__ == '__main__':
    usage = "Usage: %prog [options] [script [args]]"
    parser = OptionParser(usage)

    parser.add_option("--remoldbps", default="Y", help="remove old breakpoints")
    parser.add_option("--bpfile", help="path to breakpoints file")
    (options, args) = parser.parse_args()
    if len(args) == 0:
        rpdb2._print(parser.get_usage())
        sys.exit(1)
    winpdb = WinpdbLauncher(options.remoldbps, args)
    ret = winpdb.run(options.bpfile)
