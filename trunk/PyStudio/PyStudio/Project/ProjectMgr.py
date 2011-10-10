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
import wx

# Editra libs
import ed_glob
import ebmlib
import eclib
import ed_basewin
import syntax.synglob as synglob

# Local libs
import PyStudio.Common.Images as Images
import PyStudio.Project.ProjectXml as ProjectXml

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class ProjectManager(ed_basewin.EdBaseCtrlBox):
    """Main UI component for the Project feature."""
    PANE_NAME = u"PyProject"
    def __init__(self, parent):
        """Create the manager window
        @param parent: MainWindow instance

        """
        super(ProjectManager, self).__init__(parent)

        # Attributes
        self._mw = parent
        self._tree = ProjectTree(self)

        # Setup
        cbar = self.CreateControlBar(wx.TOP)
        self.projbtn = cbar.AddPlateButton(bmp=Images.Project.Bitmap)
        bmp = wx.ArtProvider_GetBitmap(str(synglob.ID_LANG_PYTHON), wx.ART_MENU)
        cbar.AddControl(wx.StaticLine(cbar, size=(1,16), style=wx.LI_VERTICAL))
        nfilebtn = cbar.AddPlateButton(bmp=bmp)
        nfilebtn.ToolTip = wx.ToolTip(_("New Module"))
        bmp = wx.ArtProvider_GetBitmap(str(ed_glob.ID_PACKAGE), wx.ART_MENU)
        npkgbtn = cbar.AddPlateButton(bmp=bmp)
        npkgbtn.ToolTip = wx.ToolTip(_("New Package"))
        bmp = wx.ArtProvider_GetBitmap(str(ed_glob.ID_NEW_FOLDER), wx.ART_MENU)
        nfolderbtn = cbar.AddPlateButton(bmp=bmp)
        nfolderbtn.ToolTip = wx.ToolTip(_("New Folder"))
        self.SetWindow(self._tree)

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, self.OnNewFile, nfilebtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewPackage, npkgbtn)
        self.Bind(wx.EVT_BUTTON, self.OnNewFolder, nfolderbtn)

    #---- Properties ----#
    MainWindow = property(lambda self: self._mw)
    Tree = property(lambda self: self._tree)

    #---- Implementation ----#

    def OnNewFolder(self, evt):
        pass

    def OnNewPackage(self, evt):
        pass

    def OnNewFile(self, evt):
        pass

#-----------------------------------------------------------------------------#

class ProjectTree(eclib.FileTree):
    """Provides a tree view of all the files and packages in a project."""
    def __init__(self, parent):
        super(ProjectTree, self).__init__(parent)
