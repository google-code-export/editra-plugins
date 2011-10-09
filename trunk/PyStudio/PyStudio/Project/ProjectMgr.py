###############################################################################
# Name: ProjectMgr.py                                                         #
# Purpose: Project File Manager                                               #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2011 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Project File Manager

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Dependencies

# Editra libs
import ebmlib
import eclib
import ed_basewin

# Local libs
import PyStudio.Project.ProjectXml as ProjectXml

#-----------------------------------------------------------------------------#

class ProjectManager(ed_basewin.EdBaseCtrlBox):
    """Main UI component for the Project feature."""
    def __init__(self, parent):
        super(ProjectManager, self).__init__(self)

        # Attributes
        self._tree = ProjectTree(self)

        # Setup
        cbar = self.CreateControlBar(wx.TOP)
        self.SetWindow(self._tree)

class ProjectTree(eclib.FileTree):
    """Provides a tree view of all the files and packages in a project."""
    def __init__(self, parent):
        super(ProjectTree, self).__init__(self, parent)
