###############################################################################
# Name: __init__.py                                                           #
# Purpose: Plugin to add the ability to submit code to thedailywtf.com        #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2010 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################
"""Adds Submit to TDWTF to the editor right click menu"""
__author__ = "Cody Precord"
__version__ = "0.1"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Imports
import util
import iface
import plugin
import ed_msg
import eclib
import ebmlib

#-----------------------------------------------------------------------------#
# Globals
from wx.lib.embeddedimage import PyEmbeddedImage

WTFICON = PyEmbeddedImage(
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAAZiS0dE"
    "AP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9oLCw8rCzVeQCUAAAG6"
    "SURBVDjLpdNPaM9xHMfxx/e33/p91mwtyZh2mMZlB9v3ICWSmFwnJxEnJy7KTVErl5G7g5I/"
    "KVzkRhxMkr6yaVGmuKiFmbF9SPs57DN9+yWRd30O7/fn9Xl9np/39/3lPyODIoS1OIIOzGET"
    "JjGcxzi2JC5CWIE+dGIK09UihAy7MYg2zGM9uvGyCOF5HuNC8tiOayWAIitCGMKNP1DeTGs8"
    "6XrLBlXsbzjwMVGsSflQwt6MBw0GKtiHUyl/hX48ajD9kQy3lGqzuF/JY5zLYzyJHmzDaewp"
    "Cd9jAlWEUn0clyulQi8uJKKlWMBVnEgmF1P9GYYxWYGJ1soyHMMO3EuiW9iF4+lprViV9jbg"
    "dR7jTBU+tCzP2ma/zCxkv0iu5zHuLTehCKETG/EZMc3LYlzq62u+c+Dg6k9v34R/mcIihK4M"
    "HmdZT3OtNlinHS24m8c42iDuxvlE0JX69bQKTbXaobrsKPWphDeP0YYLB7EVT9JMVLCzmobh"
    "XV29FeswXfk98eFEtzLlV/IYv1agvnjjmdT52x3fvo8snXoxPpYtxJhhBOfSp4WH5b+xH00Y"
    "yGgfiPHs3zbyJ27AfbbT4s3EAAAAAElFTkSuQmCC")

SUBMIT_TPL = """<Submit xmlns=\"http://thedailywtf.com/\">
<name>%s</name>
<emailAddress>%s</emailAddress>
<subject>%s</subject>
<comments>%s</comments>
<codeSubmission>%s</codeSubmission>
<doNotPublish>False</doNotPublish>
"""

_ = wx.GetTranslation

# Register Plugin Translation Catalogs
try:
    wx.GetApp().AddMessageCatalog('dailywtf', __name__)
except:
    pass

#-----------------------------------------------------------------------------#

ID_TDWTF = wx.NewId()
class TheDailyWtf(plugin.Plugin):
    """Adds Submit to The DailyWtf context menu"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        util.Log("[thedailywtf][info] PlugIt called")
        # Note: multiple subscriptions are ok it will only be 
        #       called once.
        ed_msg.Subscribe(self.OnContextMenu, ed_msg.EDMSG_UI_STC_CONTEXT_MENU)

    def GetMenuHandlers(self):
        """Not needed by this plugin"""
        return list()

    def GetUIHandlers(self):
        """Not needed by this plugin"""
        return list()

    def GetMinVersion(self):
        return u"0.5.86"

    #---- Implementation ----#

    @staticmethod
    def OnContextMenu(msg):
        """EdMsg Handler for customizing the buffers context menu"""
        menumgr = msg.GetData()
        menu = menumgr.GetMenu()
        if menu:
            menu.AppendSeparator()
            item = menu.Append(ID_TDWTF, _("Submit to TDWTF"))
            item.SetBitmap(WTFICON.GetBitmap())
            menumgr.AddHandler(ID_TDWTF, OnSubmit)

#-----------------------------------------------------------------------------#

def OnSubmit(buff, evt):
    """Callback for buffer context menu event.
    Opens the submission dialog
    @param buff: EditraStc
    @param evt: MenuEvent

    """
    if evt.GetId() == ID_TDWTF:
        app = wx.GetApp()
        dlg = SubmitDialog(buff, 
                           title=_("Submit your WTF"),
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        dlg.SetSenderName(wx.GetUserName())
        dlg.SetSnippetField(buff.GetSelectedText())
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            # send it
            info = dlg.GetSubmissionInfo()
            # Need to encode as UTF-8
            try:
                info = [data.encode('utf-8') for data in info]
            except UnicodeEncodeError:
                return # FAIL TODO: report error to user
            host = "http://thedailywtf.com/SubmitWTF.asmx"
            bodytxt = SUBMIT_TPL % tuple(info)
            message = ebmlib.SOAPMessage(host, bodytxt)
        else:
            pass # Canceled
    else:
        evt.Skip()

#-----------------------------------------------------------------------------#

class SubmitDialog(eclib.ECBaseDlg):
    def __init__(self, parent, *args, **kwargs):
        """Email submission dialog for sending a code snippet
        to the wtf.com.

        """
        super(SubmitDialog, self).__init__(parent, *args, **kwargs)

        # Attributes
        panel = SubmitPanel(self)

        # Setup
        self.SetIcon(WTFICON.GetIcon())
        self.SetPanel(panel)
        self.SetInitialSize((300, 350))

class SubmitPanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        super(SubmitPanel, self).__init__(parent, *args, **kwargs)

        # Attributes
        statbox = wx.StaticBox(self, label=_("Submitter Info"))
        self._hdrsz = wx.StaticBoxSizer(statbox, wx.VERTICAL)
        self._name = wx.TextCtrl(self)
        self._email = wx.TextCtrl(self)
        self._subject = wx.TextCtrl(self)
        self._msg = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self._snippet = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self._submit = wx.Button(self, wx.ID_OK, label=_("Submit"))
        self._ctrls = (self._name, self._email, self._subject,
                       self._msg, self._snippet)

        # Layout
        self.__DoLayout()

        # Event Handlers
        self.Bind(wx.EVT_UPDATE_UI, self.OnUpdateUI, self._submit)

    def __DoLayout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        headsz = wx.FlexGridSizer(3, 2, 3, 3)
        headsz.AddGrowableCol(1, 1)
        for lbl, field in ((_("Your Name: "), self._name),
                           (_("Your E-mail: "), self._email),
                           (_("Subject: "), self._subject)):
            label = wx.StaticText(self, label=lbl)
            headsz.Add(label, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
            headsz.Add(field, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 2)
        self._hdrsz.Add(headsz, 0, wx.EXPAND|wx.ALL, 5)

        sizer.Add(self._hdrsz, 0, wx.EXPAND|wx.ALL, 8)

        sizer.Add(wx.StaticText(self, label=_("Message:")),
                  0, wx.TOP|wx.LEFT, 5)
        sizer.Add(self._msg, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(wx.StaticText(self, label=_("Code Snippet:")),
                  0, wx.TOP|wx.LEFT, 5)
        sizer.Add(self._snippet, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self._submit, 0, wx.ALIGN_RIGHT|wx.ALL, 8)

        self.SetSizer(sizer)

    def OnUpdateUI(self, event):
        if event.GetEventObject() is self._submit:
            for ctrl in self._ctrls:
                val = ctrl.GetValue()
                if not val:
                    event.Enable(False)
                    break
            else:
                event.Enable(True)
        else:
            event.Skip()

    @eclib.expose(SubmitDialog)
    def GetSubmissionInfo(self):
        """Get the submission info
        @return: tuple(name, email, subject, msg, code)

        """
        values = [ctrl.GetValue() for ctrl in self._ctrls]
        return tuple(values)

    @eclib.expose(SubmitDialog)
    def SetSnippetField(self, snippet):
        self._snippet.SetValue(snippet)

    @eclib.expose(SubmitDialog)
    def SetSenderName(self, sender):
        self._name.SetValue(sender)

    @eclib.expose(SubmitDialog)
    def SetSenderEmail(self, email):
        self._email.SetValue(email)

#(defun wtf-submit-button (&rest ignore)
#  "Does the actual submit to the http://thedailywtf.com/SubmitWTF.asmx web service."
#  (let ((xml (format "<?xml version=\"1.0\" encoding=\"utf-8\"?>
#<soap12:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap12=\"http://www.w3.org/2003/05/soap-envelope\">
#<soap12:Body>
#<Submit xmlns=\"http://thedailywtf.com/\">
#<name>%s</name>
#<emailAddress>%s</emailAddress>
#<subject>%s</subject>
#<comments>%s</comments>
#<codeSubmission>%s</codeSubmission>
#<doNotPublish>%s</doNotPublish>
#</Submit>
#</soap12:Body>
#</soap12:Envelope>"
#                     (widget-value wtf-name)
#                     (widget-value wtf-email)
#                     (widget-value wtf-subject)
#                     (widget-value wtf-comment)
#                     (widget-value wtf-source)
#                     (if (widget-value wtf-dontPublish)
#                         "true"
#                       "false"))))
#    (setq wtf-proc (http-post "http://thedailywtf.com/SubmitWTF.asmx"
#                              xml
#                              "application/soap+xml; charset=utf-8"
#                              nil
#                              'wtf-response-ignore))
#    (kill-buffer (get-buffer-create "*submit-wtf*"))))

#(defun http-post (url body content-type &optional headers sentinel
#                      version verbose bufname)
#  "Post to a URL in a buffer using HTTP 1.1, and return the process.
#You can get the buffer associated with this process using
#`process-buffer'. Shamelessly ripped from http-post.el

#PARAMTERS has been replaces by body

#CONTENT-TYPE is a coding system to use. Its upper case print name
#will be used for the server. Possible values are `iso-8859-1' or
#`euc-jp' and others.

#The optional HEADERS are an alist where each element has the form
#\(NAME . VALUE). Both must be strings and will be passed along with
#the request. The reason CONTENT-TYPE is not just passed along as one
#of the headers is that part of the Content-Type value is fixed and
#cannot be changed: The basic encoding is implemented using
#`html-url-encode' and is called application/x-www-form-urlencoded.

#With optional argument SENTINEL, the buffer is not shown. It is the
#responsability of the sentinel to show it, if appropriate. A sentinel
#function takes two arguments, process and message. It is called when
#the process is killed, for example. This is useful when specifying a
#non-persistent connection. By default, connections are persistent.
#Add \(\"Connection\" . \"close\") to HEADERS in order to specify a
#non-persistent connection. Usually you do not need to specify a
#sentinel, and `ignore' is used instead, to prevent a message being
#printed when the connection is closed.

#If you want to filter the content as it arrives, bind
#`http-filter-pre-insert-hook' and `http-filter-post-insert-hook'.

#The optional argument VERSION specifies the HTTP version to use. It
#defaults to version 1.0, such that the connection is automatically
#closed when the entire document has been downloaded.

#If the optional argument VERBOSE is non-nil, a message will show the
#command sent to the server.

#The coding system of the process is set to `binary', because we need to
#distinguish between \\r and \\n. To correctly decode the text later,
#use `decode-coding-region' and get the coding system to use from
#`http-headers'."
#  (interactive)
#  (setq version (or version 1.1))
#  (let* (host dir file port proc buf header content-length)
#    (unless (string-match
#             "http://\\([^/:]+\\)\\(:\\([0-9]+\\)\\)?/\\(.*/\\)?\\([^:]*\\)"
#             url)
#      (error "Cannot parse URL %s" url))
#    (unless bufname (setq bufname
#                          (format "*HTTP POST %s *" url)))
#    (setq host (match-string 1 url)
#          port (or (and (setq port (match-string 3 url)) (string-to-int port)) 80)
#          dir (or (match-string 4 url) "")
#          file (or (match-string 5 url) "")
#          buf (get-buffer-create bufname)
#          proc (open-network-stream (concat "HTTP POST " url)
#                                    buf (if http-proxy-host http-proxy-host host) (if http-proxy-port http-proxy-port port)))
#    (set-process-sentinel proc (or sentinel 'ignore))
#    (set-process-coding-system proc 'binary 'binary); we need \r\n in the headers!
#    (set-process-filter proc 'http-filter)
#    (set-marker (process-mark proc) (point-min) buf)
#    (if sentinel
#        (set-buffer buf)
#      (switch-to-buffer buf))
#    (erase-buffer)
#    (kill-all-local-variables)
    
#    (setq header
#          (concat (format "POST %s%s%s HTTP/%.1f\r\n"
#                          (if http-proxy-host (concat "http://" host "/") "/")
#                          dir
#                          file
#                          version)
#                  (format "Host: %s\r\n" host)
#                  (format "Content-Type: %s\r\n" content-type)
#                  (format "Content-Length: %d\r\n" (length body))
#                  "Connection: close\r\n"
#                  "\r\n"))
#    (when verbose
#      (insert header body "\n\n"))
#    (print (format "%s%s%s" header body "\n\n"))
#    (process-send-string proc (concat header body "\r\n"))
#    proc))