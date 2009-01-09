import wx
import os.path

_ = wx.GetTranslation

ID_OPEN_MODULE = wx.NewId()

class OpenModuleDialog(wx.TextEntryDialog):
    """
    A Text entry dialog that returns the source file name of the input module.
    """
    _SRC_EXTENSIONS = '.py', '.pyw'
    _BYTECODE_EXTENSIONS = '.pyc', '.pyo'
    _DEFAULT_MESSAGE = _("Enter package/module name\n"
                         "(e.g 'pickle', 'wx.lib.pyshell')")
    _DEFAULT_CAPTION = _("Open module")

    def __init__(self, parent, message=_DEFAULT_MESSAGE,
                 caption=_DEFAULT_CAPTION, *args, **kwargs):
        wx.TextEntryDialog.__init__(self, parent, message, caption,
                                    *args, **kwargs)
        
    def GetValue(self):
        """Return the name of the source file of the module in the input line
        """
        name = wx.TextEntryDialog.GetValue(self)
        if not name: return None

        # Import the module to find out its file
        try:
            # fromlist needs to be non-empty to import inside packages
            # (e.g. 'wx.lib', 'distutils.core')
            module = __import__(name, fromlist=['None'])
        except ImportError:
            self.ShowWarning("No module/package named %s" % name)
            return None

        fname = getattr(module, '__file__', None)
        
        if fname:
            # Open source files instead of bytecode
            root, ext = os.path.splitext(fname)
            if ext in self._BYTECODE_EXTENSIONS:
                for se in self._SRC_EXTENSIONS:
                    if os.path.isfile(root + se):
                        fname = root + se
                        break
                else:
                    fname = None
            elif ext not in self._SRC_EXTENSIONS:
                # This is not a pure python module
                fname = None

        if fname is None:
            self.ShowWarning("No source code for %s" % name)
        
        return fname
        
    def ShowWarning(self, message):
        mdlg = wx.MessageDialog(self.GetParent(),
                                _(message),
                                self.GetTitle(),
                                wx.OK | wx.ICON_WARNING)
        mdlg.CenterOnParent()
        mdlg.ShowModal()
        mdlg.Destroy()
