###############################################################################
# Name: __init__.py                                                           #
# Purpose: Text Encoder/Decoder Tools                                         #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2012 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""Text Encoder/Decoder tools
  * Base16 encoder/decoder
  * Base32 encoder/decoder
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
import iface
import util
import ed_msg

# Local imports
import emachine

#-----------------------------------------------------------------------------#
# Globals
ID_ENIGMA = wx.NewId()
ID_BASE16_ENC = wx.NewId()
ID_BASE32_ENC = wx.NewId()
ID_BASE64_ENC = wx.NewId()
ID_BASE16_DEC = wx.NewId()
ID_BASE32_DEC = wx.NewId()
ID_BASE64_DEC = wx.NewId()

_ = wx.GetTranslation

# Register Plugin Translation Catalogs
try:
    wx.GetApp().AddMessageCatalog('Enigma', __name__)
except:
    pass

#-----------------------------------------------------------------------------#

class EnigmaPlugin(plugin.Plugin):
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

            b16enc = subMen.Append(ID_BASE16_ENC, _("Base16 Encode"))
            b32enc = subMen.Append(ID_BASE32_ENC, _("Base32 Encode"))
            b64enc = subMen.Append(ID_BASE64_ENC, _("Base64 Encode"))

            subMen.AppendSeparator()

            b16dec = subMen.Append(ID_BASE16_DEC, _("Base16 Decode"))
            b32dec = subMen.Append(ID_BASE32_DEC, _("Base32 Decode"))
            b64dec = subMen.Append(ID_BASE64_DEC, _("Base64 Decode"))

            menu.AppendMenu(ID_ENIGMA, u"Enigma", subMen)

            buf = menumgr.GetUserData('buffer')
            if buf:
                # Only enable the menu item if there is a selection in the
                # buffer.
                has_sel = buf.HasSelection()
                for item in (b16enc, b32enc, b64enc,
                             b16enc, b32enc, b64dec):
                    item.Enable(has_sel)

            for mid in (ID_BASE16_DEC, ID_BASE16_ENC,
                        ID_BASE32_DEC, ID_BASE32_ENC,
                        ID_BASE64_DEC, ID_BASE64_ENC):
                menumgr.AddHandler(mid, OnEnDe)

#-----------------------------------------------------------------------------#

_DECODERS = {ID_BASE16_DEC : "base16",
             ID_BASE32_DEC : "base32",
             ID_BASE64_DEC : "base64"}

_ENCODERS = {ID_BASE16_ENC : "base16",
             ID_BASE32_ENC : "base32",
             ID_BASE64_ENC : "base64"}

def OnEnDe(buff, evt):
    """Handle context menu events"""
    try:
        if evt.Id in _DECODERS:
            util.Log("[Enigma] Enigma Decode")
            decoder = emachine.EnigmaMachine.FactoryCreate(_DECODERS.get(evt.Id))
            txt = decoder.decode(buff.GetSelectedText())
            buff.ReplaceSelection(txt)
        elif evt.Id in _ENCODERS:
            util.Log("[Enigma] Enigma Encode")
            encoder = emachine.EnigmaMachine.FactoryCreate(_ENCODERS.get(evt.Id))
            txt = encoder.encode(buff.GetSelectedText())
            buff.ReplaceSelection(txt)
        else:
            evt.Skip()
    except Exception, msg:
        util.Log("[Enigma][err] % s" % msg)
