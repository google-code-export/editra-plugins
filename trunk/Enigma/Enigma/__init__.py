###############################################################################
# Name: __init__.py                                                           #
# Purpose: Text Encoder/Decoder Tools                                         #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2012 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""Text Encoder/Decoder tools
  * Base64 encoder/decoder

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id:  $"
__revision__ = "$Revision:  $"

#-----------------------------------------------------------------------------#
# Imports
import wx

# Editra Libs
import plugin
import util
import ed_msg

#-----------------------------------------------------------------------------#
# Globals
ID_ENIGMA = wx.NewId()
ID_BASE64_ENC = wx.NewId()
ID_BASE64_DEC = wx.NewId()

_ = wx.GetTranslation

# Register Plugin Translation Catalogs
try:
    wx.GetApp().AddMessageCatalog('Enigma', __name__)
except:
    pass

#-----------------------------------------------------------------------------#

class Enigma(plugin.Plugin):
    """Text encoder/decoder context menu plugin"""
    plugin.Implements(iface.MainWindowI)
    def PlugIt(self, parent):
        util.Log("[Enigma][info] PlugIt called")
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
        return u"0.7.00"

    #---- Implementation ----#

    @staticmethod
    def OnContextMenu(msg):
        """EdMsg Handler for customizing the buffers context menu"""
        menumgr = msg.GetData()
        menu = menumgr.GetMenu()
        if menu:
            menu.AppendSeparator()

            # Build Submenu
            subMen = wx.Menu()

            b64enc = subMen.Append(ID_BASE64_ENC, _("Base64 Encode"))
            b64dec = subMen.Append(ID_BASE64_DEC, _("Base64 Decode"))

            menu.AppendMenu(ID_ENIGMA, u"Enigma", subMen)

            buf = menumgr.GetUserData('buffer')
            if buf:
                # Only enable the menu item if there is a selection in the
                # buffer.
                has_sel = buf.HasSelection()
                for item in (b64enc, b64dec):
                    item.Enable(has_sel)

            menumgr.AddHandler(ID_BASE64_ENC, OnEnDe)
            menumgr.AddHandler(ID_BASE64_DEC, OnEnDe)

#-----------------------------------------------------------------------------#

def OnEnDe(buff, evt):
    """Handle context menu events"""
    if evt.Id == ID_BASE64_DEC:
        util.Log("[Enigma] Base64 Decode")
        pass
    elif evt.Id == ID_BASE64_ENC:
        util.Log("[Enigma] Base64 Encode")
        pass
    else:
        evt.Skip()
