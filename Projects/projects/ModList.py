###############################################################################
# Name: ModList.py                                                            #
# Purpose: Enumerate modified, added, deleted files in a list                 #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
File Modification List

Display component for displaying file status for a repository and allowing for
checking, reverts, ect...

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#--------------------------------------------------------------------------#
# Imports
import wx
import wx.lib.mixins.listctrl as listmix

# For Testing
import sys
import os
path = os.path.abspath('..\\..\\..\\..\\src')
sys.path.insert(0, path)

# Local Imports
import FileIcons
import ConfigDialog
import ScCommand

# Editra Imports
import ed_glob

#ed_glob.CONFIG['CACHE_DIR'] = "/Users/codyprecord/.Editra/cache/"
ed_glob.CONFIG['CACHE_DIR'] = "C:\\Documents and Settings\\cjprecord\\.Editra\\cache\\"
import eclib.ctrlbox as ctrlbox
import eclib.platebtn as platebtn
import eclib.elistmix as elistmix

#--------------------------------------------------------------------------#
# Globals

# Menu Id's
ID_COMPARE_TO_PREVIOUS = wx.NewId()
ID_COMMIT = wx.NewId()
ID_REVERT = wx.NewId()
ID_REVISION_HIST = wx.NewId()

# Control Id's
ID_REPO_CHOICE = wx.NewId()


# Status Keys used by SourceControl modules
STATUS = { u'modified' : u'M',
           u'added'    : u'A',
           u'deleted'  : u'D',
           u'conflict' : u'C',
           u'unknown'  : u'?' }
           
_ = wx.GetTranslation

#--------------------------------------------------------------------------#

class RepoModBox(ctrlbox.ControlBox):
    """Repository modification list container window"""
    def __init__(self, parent):
        ctrlbox.ControlBox.__init__(self, parent)

        # Attributes
        self._list = RepoModList(self)
        self._config = ConfigDialog.ConfigData() # Singleton Config Obj
        self._crepo = 0
        self._repos = self._config['projects'].keys()
        self._repo_ch = None

        # Setup
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_BUTTON, lambda evt: self.DoCommit(), id=ID_COMMIT)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.DoStatusRefresh(), id=wx.ID_REFRESH)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.DoRevert(), id=wx.ID_REVERT)
        self.Bind(wx.EVT_CHOICE, self.OnChoice, id=ID_REPO_CHOICE)

    def __DoLayout(self):
        """Layout and setup the results screen ui"""
        ctrlbar = ctrlbox.ControlBar(self, style=ctrlbox.CTRLBAR_STYLE_GRADIENT)
        if wx.Platform == '__WXGTK__':
            ctrlbar.SetWindowStyle(ctrlbox.CTRLBAR_STYLE_DEFAULT)

        def cmptup(x, y):
            if x[1] < y[1]:
                return -1
            elif x[1] == y[1]:
                return 0
            else:
                return 1

        # Repository
        ctrlbar.AddControl(wx.StaticText(ctrlbar, label=_("Repository") + u":"))
        projects = sorted([(x, os.path.basename(x)) for x in self._repos], cmptup)
        self._repos = [x[0] for x in projects]
        self._repo_ch = wx.Choice(ctrlbar, ID_REPO_CHOICE,
                                  choices=[x[1] for x in projects])
        if len(self._repos):
            self._repo_ch.SetToolTipString(self._repos[0])
        ctrlbar.AddControl(self._repo_ch)

        ctrlbar.AddStretchSpacer()

        # Commit
        commit = platebtn.PlateButton(ctrlbar, ID_COMMIT, _("Commit"),
                                      FileIcons.getScCommitBitmap(),
                                      style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(commit, wx.ALIGN_RIGHT)

        # Refresh Button
        refresh = platebtn.PlateButton(ctrlbar, wx.ID_REFRESH, _("Refresh"),
                                       FileIcons.getScStatusBitmap(),
                                       style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(refresh, wx.ALIGN_RIGHT)

        # Clear Button
        revert = platebtn.PlateButton(ctrlbar, ID_REVERT, _("Revert"),
                                      FileIcons.getScRevertBitmap(),
                                      style=platebtn.PB_STYLE_NOBG)
        ctrlbar.AddControl(revert, wx.ALIGN_RIGHT)

        ctrlbar.SetVMargin(1, 1)
        self.SetControlBar(ctrlbar)
        self.SetWindow(self._list)

    def DoCommit(self):
        """Commit the selected files"""
        self._list.CommitSelectedFiles()

    def DoRevert(self):
        """Revert the selected files"""
        

    def DoStatusRefresh(self):
        """Refresh the status of the currently selected repository"""
        path = self._repos[self._crepo]
        self._list.UpdatePathStatus(path)

    def OnChoice(self, evt):
        """Handle changes in selection of the current repo"""
        if evt.GetId() == ID_REPO_CHOICE:
            self._crepo = self._repo_ch.GetSelection()
            self._repo_ch.SetToolTipString(self._repos[self._crepo])
            self.DoStatusRefresh()
        else:
            evt.Skip()

#--------------------------------------------------------------------------#

class RepoModList(wx.ListCtrl,
                  elistmix.ListRowHighlighter,
                  listmix.ListCtrlAutoWidthMixin):
    """List for managing and listing files under SourceControl.
    Specifically it displays the summary of modified files under a given
    repository.

    """
    STATUS_COL = 0
    FILENAME_COL = 1
    def __init__(self, parent, id=wx.ID_ANY):
        """Create the list control"""
        wx.ListCtrl.__init__(self, parent, id,
                             style=wx.LC_REPORT | wx.LC_VRULES | wx.BORDER)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        elistmix.ListRowHighlighter.__init__(self)

        # Attributes
        self._menu = None
        self._items = list()
        self._path = None
        self._ctrl = ScCommand.SourceController(self)

        # Setup
        self.InsertColumn(RepoModList.STATUS_COL, _("Status"),
                          wx.LIST_FORMAT_CENTER)
        self.InsertColumn(RepoModList.FILENAME_COL, _("Filename"))

        # Event Handlers
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnActivated)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_MENU, self.OnMenu)
        self.Bind(ScCommand.EVT_STATUS, self.OnStatus)

    def AddFile(self, status, fname):
        """Add a file to the list
        @param status: Status indicator
        @param fname: File name

        """
        self._items.append(dict(status=status, fname=fname))
        self.Append((status, fname))

    def DeleteAllItems(self):
        """Clear the list"""
        for item in range(len(self._items)):
            self._items.pop()
        wx.ListCtrl.DeleteAllItems(self)

    def CommitSelectedFiles(self):
        """Commit the selected files"""
        paths = self.GetSelectedPaths()
        print paths
#        self._ctrl.

    def GetSelectedPaths(self):
        """Get the paths of the selected items
        @return: list of strings

        """
        items = list()
        idx = -1
        while True:
            item = self.GetNextItem(idx, state=wx.LIST_STATE_SELECTED)
            if item == wx.NOT_FOUND:
                break
            else:
                items.append(item)
                idx = item

        paths = list()
        for idx in items:
            item = self.GetItem(idx, RepoModList.FILENAME_COL)
            path = item.GetText()
            if path:
                paths.append(path)

        return paths

    def RefreshStatus(self):
        """Refresh the screen with the latest status info from the
        current repository.

        """
        self.DeleteAllItems()
        if self._path is not None:
            self.UpdatePathStatus(self._path)

    def UpdatePathStatus(self, path):
        """Run an status update job
        @param path: path to check status on

        """
        src_c = self._ctrl.GetSCSystem(path)
        if src_c is not None:
            self._path = path
            self._ctrl.StatusWithTimeout(src_c, None,
                                         dict(path=path),
                                         recursive=True)

    #---- Event Handlers ----#

    def OnActivated(self, evt):
        """Open the file in the editor"""
        evt.Skip()

    def OnContextMenu(self, evt):
        """Show the context menu"""
        if not self.GetSelectedItemCount():
            evt.Skip()
            return

        if self._menu is None:
            # Create the menu once
            self._menu = wx.Menu()
            item = self._menu.Append(ID_COMPARE_TO_PREVIOUS,
                                     _("Compare to previous version"))
            item.SetBitmap(FileIcons.getScDiffBitmap())
            item = self._menu.Append(ID_REVISION_HIST,
                                     _("Show revision history"))
            item.SetBitmap(FileIcons.getScHistoryBitmap())
            item = self._menu.Append(ID_COMMIT,
                                     _("Commit changes"))
            item.SetBitmap(FileIcons.getScCommitBitmap())
            item = self._menu.Append(ID_REVERT,
                                     _("Revert to repository version"))
            item.SetBitmap(FileIcons.getScRevertBitmap())

        self.PopupMenu(self._menu)

    def OnMenu(self, evt):
        """Handler for menu events from context menu"""
        e_id = evt.GetId()
        if e_id == ID_COMPARE_TO_PREVIOUS:
            # Do Diff
            pass
        elif e_id == ID_COMMIT:
            # Checkin
            pass
        elif e_id == ID_REVERT:
            # Revert changes
            pass
        elif e_id == ID_REVISION_HIST:
            # Show the history of the selected file
            pass
        elif e_id == wx.ID_REFRESH:
            # Refresh the status
            pass
        else:
            evt.Skip()

    def OnStatus(self, evt):
        """Handler for the status command event. Updates the list with
        the status of the files from the selected repository.

        """
        status = evt.GetValue()[1:]

        path = None
        if len(status):
            path = status[0].get('path', None)
            status = status[1]

        if path is None:
            # TODO: notify that the status check failed
            return

        # Clear the display
        self.DeleteAllItems()

        # Update the display
        for fname, stat in status.iteritems():
            fstatus = stat.get('status', 'uptodate')
            if fstatus != 'uptodate':
                self.AddFile(STATUS.get(fstatus, u'U'),
                             os.path.join(path, fname))

#--------------------------------------------------------------------------#

if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None)
    box = RepoModBox(frame)
    frame.Show()
    app.MainLoop()

