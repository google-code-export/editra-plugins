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
                            _('The requested file could not '
                              'be retrieved from the source '
                              'control system.'),
                            _('Could not retrieve file'),
                            style=wx.OK|wx.ICON_ERROR)
    rval = dlg.ShowModal()
    dlg.Destroy()
    return rval
