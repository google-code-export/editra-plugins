###############################################################################
# Name: ProjCmnDlg.py                                                         #
# Purpose: Common dialogs                                                     #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Projects Common Dialogs

Common Dialog functions and classes

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import os

#-----------------------------------------------------------------------------#
# Globals

_ = wx.GetTranslation

#-----------------------------------------------------------------------------#
# Message Dialogs

def RetrievalErrorDlg(parent):
    """Show an error dialog for a retrieval error
    @param parent: parent window
    @return: ID_OK

    """
    dlg = wx.MessageDialog(self,
                            _('The requested file could not be retrieved from '
                              'the source control system.'),
                            _('Could not retrieve file'),
                            style=wx.OK|wx.ICON_ERROR)
    rval = dlg.ShowModal()
    dlg.Destroy()
    return rval

#-----------------------------------------------------------------------------#

class CommitDialog(wx.Dialog):
    """Dialog for entering commit messages"""
    def __init__(self, parent, title=u'', caption=u'', default=list()):
        """Create the Commit Dialog
        @keyword default: list of file names that are being commited

        """
        wx.Dialog.__init__(self, parent, title=title)

        # Attributes
        self._caption = wx.StaticText(self, label=caption)
        self._commit = wx.Button(self, wx.ID_OK, _("Commit"))
        self._commit.SetDefault()
        self._cancel = wx.Button(self, wx.ID_CANCEL)

        self._entry = wx.TextCtrl(self, size=(400, 250), \
                                  style=wx.TE_MULTILINE|wx.TE_RICH2)
        font = self._entry.GetFont()
        if wx.Platform == '__WXMAC__':
            font.SetPointSize(12)
            self._entry.MacCheckSpelling(True)
        else:
            font.SetPointSize(10)
        self._entry.SetFont(font)

        self._DefaultMessage(default)
        self._entry.SetFocus()

        # Layout
        self._DoLayout()
        self.CenterOnParent()

    def _DefaultMessage(self, files):
        """
        Put the default message in the dialog and the given list of files

        """
        msg = list()
        msg.append(u': ' + (u'-' * 40))
        msg.append(u": Lines beginning with `:' are removed automatically")
        msg.append(u": Modified Files:")
        for path in files:
            tmp = ":\t%s" % path
            msg.append(tmp)
        msg.append(u': ' + (u'-' * 40))
        msg.extend([u'', u''])
        msg = os.linesep.join(msg)
        self._entry.SetValue(msg)
        self._entry.SetInsertionPoint(self._entry.GetLastPosition())

    def _DoLayout(self):
        """ Used internally to layout dialog before being shown """
        sizer = wx.BoxSizer(wx.VERTICAL)
        csizer = wx.BoxSizer(wx.HORIZONTAL)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        esizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add((10, 10), 0)
        csizer.Add((10, 10), 0)
        csizer.Add(self._caption, 0, wx.ALIGN_LEFT, 5)
        sizer.Add(csizer, 0)
        sizer.Add((10, 10), 0)
        esizer.AddMany([((10, 10), 0),
                        (self._entry, 1, wx.EXPAND),
                        ((10, 10), 0)])
        sizer.Add(esizer, 0, wx.EXPAND)
        bsizer.AddStretchSpacer()
        bsizer.AddMany([(self._cancel, 0, wx.ALIGN_RIGHT, 5), ((5, 5)),
                       (self._commit, 0, wx.ALIGN_RIGHT, 5), ((5, 5))])
        sizer.Add((10, 10))
        sizer.Add(bsizer, 0, wx.ALIGN_RIGHT)
        sizer.Add((10, 10))
        self.SetSizer(sizer)
        self.SetInitialSize()

    def GetValue(self):
        """Return the value of the commit message"""
        txt = self._entry.GetString(0, self._entry.GetLastPosition()).strip()
        txt = txt.replace('\r\n', '\n')
        return os.linesep.join([ x for x in txt.split('\n')
                                 if not x.lstrip().startswith(':') ])

#-----------------------------------------------------------------------------#

# XXX: Doesn't seem to be used
class ExecuteCommandDialog(wx.Dialog):
    """ Creates a dialog for getting a shell command to execute """
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id, _('Execute command on files'))

        sizer = wx.BoxSizer(wx.VERTICAL)

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(self, -1,
            _('Enter a command to be executed on all selected files ' \
              'and files in selected directories.')))

        sizer.Add(hsizer)
        sizer.Add(self.CreateButtonSizer(wx.OK|wx.CANCEL), wx.ALIGN_RIGHT)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
