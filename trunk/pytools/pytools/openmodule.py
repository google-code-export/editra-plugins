###############################################################################
# Name: openmodule.py                                                         #
# Purpose:                                                                    #
# Author: Rudi Pettazzi <rudi.pettazzi@gmail.com>, Ofer Schwarz               #
# Copyright: (c) 2009 Cody Precord <staff@editra.org>                         #
# License:                                                                    #
###############################################################################

"""Open module Dialog"""

__author__ = ""
__svnid__ = "$Id$"
__revision__ = "$Revision$"

#-----------------------------------------------------------------------------#
# Imports
import wx
import sys
import os.path

#-----------------------------------------------------------------------------#
# Globals
_ = wx.GetTranslation

#-----------------------------------------------------------------------------#

class OpenModuleDialog(wx.Dialog):
    """ A dialog to find the source file of a module and open it into the
    editor notebook
    """
    # TODO: the extensions for source files could also be retrieved from
    #       syntax.syntax.ExtensionRegister
    _SRC_EXTENSIONS = '.py', '.pyw'
    _BYTECODE_EXTENSIONS = '.pyc', '.pyo'

    def __init__(self, parent, caption=u'', *args, **kwargs):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, caption,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,
                           size=(400, 230), *args, **kwargs)

        # Attributes
        self.search = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.search.ShowCancelButton(True)
        self.btnOk = wx.Button(self, wx.ID_OK, label=_('Ok'))
        self.btnOk.Enable(False)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, label=_('Cancel'))
        self.listBox = wx.ListBox(self)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, self.btnOk)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.OnConfirm, self.listBox)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.btnCancel)

    def __DoLayout(self):
        """Layout the dialog"""
        label1 = wx.StaticText(self, label=_('Find and open a module by name'))
        labsizer1 = wx.BoxSizer(wx.HORIZONTAL)
        labsizer1.Add(label1, 1, wx.ALL, 5)

        txtsizer = wx.BoxSizer(wx.HORIZONTAL)
        txtsizer.Add(self.search, 1, wx.ALL, 5)

        dsizer = wx.BoxSizer(wx.HORIZONTAL)
        divider = wx.StaticLine(self, size=(-1, 1))
        dsizer.AddMany([((5, 5), 0), (divider, 1), ((5, 5), 0)])

        label2 = wx.StaticText(self, label=_('Matching items') + u":")
        labsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        labsizer2.Add(label2, 1, wx.ALL, 5)

        lstsizer = wx.BoxSizer(wx.HORIZONTAL)
        lstsizer.Add(self.listBox, 1, wx.ALL|wx.EXPAND, 5)
        lstvsizer = wx.BoxSizer(wx.VERTICAL)
        lstvsizer.Add(lstsizer, 1, wx.EXPAND)

        bsizer = wx.StdDialogButtonSizer()
        bsizer.AddButton(self.btnOk)
        bsizer.AddButton(self.btnCancel)
        bsizer.Realize()

        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.AddMany([(labsizer1, 0), (txtsizer, 0, wx.EXPAND),
                            ((5, 5), 0), (dsizer, 0, wx.EXPAND), ((5, 5), 0),
                            (labsizer2, 0),
                            (lstvsizer, 2, wx.EXPAND), (bsizer, 0, wx.EXPAND),
                            ((5, 5), 0)])

        self.SetSizer(mainsizer)

    def OnConfirm(self, evt):
        # TODO open file in editor (readonly?)
        n = self.listBox.GetSelection()
        if n:
            filename = self.listBox.GetString(n)
            print 'opening %s in editra' % filename

    def OnCancel(self, evt):
        self.Destroy()

    def OnCancelSearch(self, evt):
        self.search.SetValue('')
        self.listBox.Set([])

    def OnSearch(self, evt):
        """Handle search events from the SearchCtrl"""
        files = self.FindModule(self.search.GetValue())
        if not files:
            self.listBox.Set([])
            return
        self.listBox.Set(files)
        self.listBox.SetSelection(0)
        self.btnOk.Enable(True)

    def FindModule(self, text):
        """Return a list with the names of the source files that matched the
        the input line (actually,  an exact match at the moment, so a single
        file at most)

        """
        if not text:
            return None

        # Import the module to find out its file
        # fromlist needs to be non-empty to import inside packages
        # (e.g. 'wx.lib', 'distutils.core')
        try:
            lst = text.split('.')
            module = __import__(text, lst[:-1])
        except ImportError:
            return None

        fname = getattr(module, '__file__', None)

        # FIXME maybe unload (del) the module? (unless already loaded before search started)
        if fname:
            # Open source files instead of bytecode
            root, ext = os.path.splitext(fname)
            if ext in OpenModuleDialog._BYTECODE_EXTENSIONS:
                for se in OpenModuleDialog._SRC_EXTENSIONS:
                    if os.path.isfile(root + se):
                        fname = root + se
                        break
                else:
                    fname = None
            elif ext not in OpenModuleDialog._SRC_EXTENSIONS:
                # This is not a pure python module
                fname = None

        return [ fname ]

#-----------------------------------------------------------------------------#
# Test
class MyApp(wx.App):
    def OnInit(self):
        dialog = OpenModuleDialog(None, "Find module")
        dialog.ShowModal()
        if dialog:
            dialog.Destroy()
        return True

if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()



