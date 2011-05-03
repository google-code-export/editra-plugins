# -*- coding: utf-8 -*-
# Name: PythonDebugger.py
# Purpose: Rpdb2 plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Rpdb2 module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import os.path
import pkg_resources

# Local Imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.PyToolsUtils import RunProcInThread
from PyTools.Common.AsyncProcessCreator import AsyncProcessCreator
from PyTools.Debugger.AbstractDebugger import AbstractDebugger
from PyTools.Debugger.RpdbDebugger import RpdbDebugger

# Editra Libraries
import util
import ebmlib

# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class PythonDebugger(AbstractDebugger):
    def __init__(self, variabledict, debuggerargs, programargs, 
        filename, debuggeewindow):
        super(PythonDebugger, self).__init__(variabledict, debuggerargs, 
            programargs, filename, debuggeewindow)

        # Attributes
        self.debuggerattachedtext = _("Debugger attached. Debuggee output starts now...\n\n")
        self.debuggerdetachedtext = _("")
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.rpdb2args = ["-d"]
        if not self.debuggerargs:
            self.debuggerargs = variabledict.get("DEBUGGERARGS")
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.debuggee = None
        self.processcreator = None

    def RunDebuggee(self):
        """Run rpdb2args"""
        flag, localpythonpath = ToolConfig.GetPythonExecutablePath("PyDbg")
        # TODO: convert errors to error codes and translate to meaningful
        #       messages on main thread.
        if not flag:
            # No configured Python
            return [(u"No Python", localpythonpath, u"NA"),]

        # No rpdb2 found in plugin
        if not pkg_resources.resource_exists("rpdb2", "rpdb2.py"):
            return ["No rpdb2 found"]

        rpdb2_script = pkg_resources.resource_filename("rpdb2", "rpdb2.py")

        if wx.Platform == "__WXMSW__":        
            self.rpdb2args += ["--pwd=%s" % RpdbDebugger.password]
        else:
            rpdb2_pw = os.path.join(os.path.dirname(rpdb2_script), "rpdbpw.txt")
            self.rpdb2args += ["--rid=%s" % rpdb2_pw]
        
        childPath, parentPath = PyToolsUtils.get_packageroot(self.filename)

        # Start rpdb2
        cmdargs = ""
        debuggee = childPath
        if self.debuggerargs:
            cmdargs = self.debuggerargs.split(" ")
            for i, cmd in enumerate(cmdargs):
                if cmd == "%SCRIPT%":
                    cmdargs[i] = debuggee
                elif cmd == "%MODULE%":
                    debuggee = PyToolsUtils.get_modulepath(childPath)
                    cmdargs[i] = debuggee

            cmdargs = self.rpdb2args + cmdargs
        else:
            cmdargs = self.rpdb2args + [debuggee,]
        allargs = cmdargs
        if self.programargs:
            allargs = allargs + self.programargs.split(" ")
        rpdb2_cmd = [localpythonpath, "-u", rpdb2_script] + allargs
        text = ""
        if self.pythonpath:
            text += "Using PYTHONPATH + %s\n" % u", ".join(self.pythonpath)
        text += "Rpdb2 command line: %s" % " ".join(rpdb2_cmd)
        text += "\nDirectory Variables file: %s\n\n" % self.dirvarfile
        self.debuggeewindow.SetText(_(text))
        self.debuggeewindow.calldebugger = self.RunDebugger
        RpdbDebugger().debuggerattachedtext = self.debuggerattachedtext
        RpdbDebugger().debuggerdetachedtext = self.debuggerdetachedtext
        RpdbDebugger().remoteprocess = False
        self.processcreator = AsyncProcessCreator(self.debuggeewindow, self.UpdateOutput, "PyDbg", parentPath, rpdb2_cmd, self.pythonpath)
        self.processcreator.start()
        util.Log("[PyDbg][info] Rpdb2 command running")

    def UpdateOutput(self, txt):
        """Check to prevent PyDeadObjectErrors"""
        if self.debuggeewindow:
            self.debuggeewindow.AppendUpdate(txt)

    def RunDebugger(self):                    
        self.debuggeewindow.calldebugger = None
        self.processcreator.restorepath()
        worker = RunProcInThread("Debug", None, RpdbDebugger().attach, self.processcreator)
        worker.start()
