# -*- coding: utf-8 -*-
# Name: PythonDebugger.py
# Purpose: Rpdb2 plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Rpdb2 module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id: PythonDebugger.py 1053 2011-02-08 22:09:37Z rans@email.com $"
__revision__ = "$Revision: 1053 $"

#-----------------------------------------------------------------------------#
# Imports
import os
import sys
import pkg_resources

# Local Imports
import ToolConfig
from PyToolsUtils import PyToolsUtils
from ProcessRunner import ProcessRunner
from AbstractDebugger import AbstractDebugger
from DebugClient import DebugClient

# Editra Imports
import util
import ebmlib

#-----------------------------------------------------------------------------#

class PythonDebugger(AbstractDebugger):
    def __init__(self, variabledict, filename):
        super(PythonDebugger, self).__init__(variabledict, filename)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.rpdb2args = ["-d", "--pwd=%s" % DebugClient.password]
        rpdb2args = variabledict.get("RPDB2ARGS")
        if rpdb2args:
            self.rpdb2args = rpdb2args
        else:
            self.rpdb2args = ""
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.nopythonerror = u"***  FATAL ERROR: No local Python configured or found"
        self.debugclient = DebugClient()

    def DoCheck(self):
        """Run rpdb2args"""

        # Figure out what Python to use
        # 1) First check configuration
        # 2) Second check for it on the path
        localpythonpath = ToolConfig.GetConfigValue(ToolConfig.TLC_PYTHON_PATH)
        if not localpythonpath:
            localpythonpath = PyToolsUtils.GetDefaultPython()

        # No configured Python
        if not localpythonpath:
            return [(u"No Python", self.nopythonerror, u"NA"),]
        util.Log("[PyDbg][info] Using Python: %s" % localpythonpath)

        # No rpdb2 found in plugin
        if not pkg_resources.resource_exists("PyTools", "rpdb2.py"):
            return ["No rpdb2 found"]

        rpdb2_script = pkg_resources.resource_filename("PyTools", "rpdb2.py")

        childPath, parentPath = PyToolsUtils.get_packageroot(self.filename)

        # Start rpdb2
        modpath = PyToolsUtils.get_modulepath(childPath)
        if ebmlib.IsUnicode(modpath):
            # Convert to string
            modpath = modpath.encode(sys.getfilesystemencoding())
        allargs = self.rpdb2args + [modpath,]
        rpdb2_cmd = [localpythonpath, rpdb2_script, allargs]
        util.Log("[PyDbg][info] Starting command: %s" % repr(rpdb2_cmd))
        processrunner = ProcessRunner(self.pythonpath)
        processrunner.runprocess(rpdb2_cmd, ".")
        processrunner.restorepath()
        # Attach Editra debug client
        self.debugclient.attach(modpath)
        processrunner.terminate()
        rows = []
        if self.pythonpath:
            rows.append((u"***", u"Using PYTHONPATH + %s"\
                          % u", ".join(self.pythonpath), u"NA"))
        rows.append((u"***", u"Rpdb2 command line: %s" % " ".join(rpdb2_cmd), u"NA"))
        rows.append((u"***", u"Directory Variables file: %s" % self.dirvarfile, u"NA"))
        util.Log("[PyDbg][info] Rpdb2 command finished running")
        return rows
