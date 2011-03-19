# -*- coding: utf-8 -*-
# Name: PythonModuleFinder.py
# Purpose: ModuleFinder plugin
# Author: Mike Rans
# Copyright: (c) 2010 Mike Rans
# License: wxWindows License
##############################################################################
""" Pylint module for Python data """

__author__ = "Mike Rans"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import os
import pkg_resources

# Local Imports
from PyTools.Common import ToolConfig
from PyTools.Common.PyToolsUtils import PyToolsUtils
from PyTools.Common.ProcessCreator import ProcessCreator
from PyTools.ModuleFinder.AbstractModuleFinder import AbstractModuleFinder

# Editra Libraries
import util
import ebmlib

#-----------------------------------------------------------------------------#

class PythonModuleFinder(AbstractModuleFinder):
    def __init__(self, variabledict, moduletofind):
        super(PythonModuleFinder, self).__init__(variabledict, moduletofind)

        # Attributes
        self.dirvarfile = variabledict.get("DIRVARFILE")
        self.pythonpath = variabledict.get("PYTHONPATH")
        self.nopythonerror = u"***  FATAL ERROR: No local Python configured or found"

    def RunModuleFind(self):
        """Run Module Finder"""

        flag, localpythonpath = ToolConfig.GetPythonExecutablePath("PyFind")

        if not flag:
            # No configured Python
            return [localpythonpath]

        # No findmodule found in plugin
        if not pkg_resources.resource_exists("PyTools.ModuleFinder", "findmodule.py"):
            return ["No findmodule found"]

        findmodule_script = pkg_resources.resource_filename("PyTools.ModuleFinder", "findmodule.py")

        # Start find module
        finder_cmd = [localpythonpath, findmodule_script, self.moduletofind]
        processcreator = ProcessCreator("PyFind", ".", finder_cmd, self.pythonpath)
        process = processcreator.createprocess()
        stdoutdata, stderrdata = process.communicate()
        processcreator.restorepath()

        util.Log("[PyFind][info] stdout %s" % stdoutdata)
        util.Log("[PyFind][info] stderr %s" % stderrdata)
        util.Log("[PyFind][info] PyFind command finished running")
        try:
            stdoutrows = eval(stdoutdata.rstrip('\r\n'))
            rows = []
            if self.pythonpath:
                rows.append(u"INFO: Using PYTHONPATH + %s"\
                              % u", ".join(self.pythonpath))
            rows.append(u"INFO: PyFind command line: %s" % " ".join(finder_cmd))
            rows.append(u"INFO: Directory Variables file: %s" % self.dirvarfile)
            return rows + stdoutrows
        except Exception, ex:
            msg = repr(ex)
            util.Log("[PyFind][info] Error: %s" % msg)
            return [msg]
        return ["Unknown error!"]
