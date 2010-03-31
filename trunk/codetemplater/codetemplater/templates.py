###############################################################################
# Name: templates.py                                                          #
# Purpose: User interface and template classes for CodeTemplater              #
# Author: Erik Tollerud <erik.tollerud@gmail.com>                             #
# Copyright: (c) 2010 Erik Tollerud <erik.tollerud@gmail.com>                 #
# License: wxWindows License                                                  #
###############################################################################

"""CodeTemplater UI and CodeTemplate class"""
__author__ = "Erik Tollerud"
__version__ = "0.1"

#-----------------------------------------------------------------------------#

import wx                   
import iface
import plugin
from os import path
from string import Template

from ed_glob import CONFIG,SB_INFO,ID_RELOAD_ENC
from ed_menu import EdMenu
from syntax import synglob,syntax
from profiler import Profile_Get, Profile_Set, Profile_Del
_ = wx.GetTranslation

PROFILE_KEY_TEMPLATES = 'CodeTemplater.Templates'

class CodeTemplate(object):
    """
    a template for use with the CodeTemplater editra plugin
    """
    
    def __init__(self,name,templatestr,description=u'',indent=True):
        self.name = name
        self.templ = Template(templatestr)
        self.description = description
        self.indent = indent
    
        
    def DoTemplate(self, page):
        seltext = page.GetSelectedText().strip()
        
        submap = {}
        seltext.strip()
        submap['same'] = seltext
        if len(seltext) > 0:
            submap['upper'] = seltext[0].upper()+seltext[1:]
            submap['lower'] = seltext[0].lower()+seltext[1:]
        else:
            submap['upper'] = submap['lower'] = seltext
        wx.GetApp().GetLog()("[CodeTemplater][info] Applying template %s to %s"%(self.name,submap['same']))
        
        if self.indent:
            #compute indentation
            line = page.GetCurrentLine()
            indent =  page.GetTabWidth() if page.GetIndentChar()=='\t' else page.GetIndent()
            indentcount = page.GetLineIndentation(line)/indent
            indentstr = page.GetIndentChar()*indentcount
        else:
            indentstr = u''
        if seltext != '':
            page.DeleteBack()
        propstring = self.templ.safe_substitute(submap)
        propstring = propstring.replace('\t',page.GetIndentChar())
        fullstring = propstring.replace('\n',page.GetEOLChar()+indentstr)
        if '#CUR' in fullstring:
            curind = fullstring.index('#CUR')
            curoffset = len(fullstring)-4-curind
            fullstring = fullstring.replace('#CUR','',1)
        else:
            curoffset = None
        page.AddText(fullstring)
        if curoffset is not None:
            newpos = page.GetCurrentPos()-curoffset
            page.SetCurrentPos(newpos)
            page.SetSelection(newpos,newpos)

class TemplateEditorDialog(wx.Dialog):
    def __init__(self, parent, plugin, ID, title, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE,
                 initiallang=None):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        
        basesizer = wx.BoxSizer(wx.VERTICAL)
        
        self.edpanel = TemplateEditorPanel(self,plugin,initiallang,-1)
        basesizer.Add(self.edpanel,0)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        basesizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        okbtn = wx.Button(self, wx.ID_CLOSE)
        okbtn.Bind(wx.EVT_BUTTON, self.OnClose)
        btnsizer.Add(okbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        profbtn = wx.Button(self, wx.ID_SAVE,_('Save'))
        profbtn.SetToolTipString(_('Save to the Profile to be reloaded on next Startup'))
        profbtn.Bind(wx.EVT_BUTTON, self.OnSaveProfile)
        btnsizer.Add(profbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        resetbtn = wx.Button(self, wx.ID_RESET,_('Reset to defaults'))
        resetbtn.SetToolTipString(_('Resets the Profile to default as well as the Current Setup'))
        resetbtn.Bind(wx.EVT_BUTTON, self.OnResetProfile)
        btnsizer.Add(resetbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        basesizer.Add(btnsizer,0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(basesizer)
        basesizer.Fit(self)
    
    def OnSaveProfile(self,reset=False):
        #profile key should be in language name
        #d = dict([(synglob.GetDescriptionFromId(k),v) for k,v in tempd.iteritems()])
        #translate template objects into their dict instead of CodeTemplate objects
        self.edpanel.ApplyTemplateInfo(updatelistind=self.edpanel.lastind)
        
        newd = {}
        
        for lang,ld in self.edpanel.plugin.templates.iteritems():
            newld = {}
            for k,v in ld.iteritems():
                newld[k] = v.__dict__.copy()
                newld[k]['templ'] = newld[k]['templ'].template
            newd[synglob.GetDescriptionFromId(lang)] = newld
        
        Profile_Set(PROFILE_KEY_TEMPLATES,newd)
    
    def OnResetProfile(self,evt):
        Profile_Set(PROFILE_KEY_TEMPLATES,None)
        self.edpanel.plugin.templates = load_templates()
        self.edpanel.listbox.SetItems(self.edpanel.GetTemplateNames())
        
    def OnClose(self,evt):
        self.Destroy()
        
        
        
class TemplateEditorPanel(wx.Panel):
    def __init__(self,parent,plugin,initiallang=None, *args, **kwargs):
        wx.Panel.__init__(self,parent, *args, **kwargs)
        self.plugin = plugin
        self.removing = False
        self.lastind = None
        self.lastname = ''
        
        basesizer = wx.BoxSizer(wx.HORIZONTAL)
        
        #left side of panel to display and alter list of templates
        listsizer = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(self, -1, _("Code Templates"))
        listsizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        langchoices = get_language_list()
        
        if isinstance(initiallang,basestring):
            id = synglob.GetIdFromDescription(initiallang)
        else:
            id = initiallang
            initiallang = synglob.GetDescriptionFromId(initiallang)
        
        if initiallang is None or initiallang not in langchoices:
            initiallang = langchoices[0]
            
        self.lastlangstr = initiallang
        
        self.langchoice = wx.Choice(self, -1, choices=langchoices)
        self.langchoice.SetSelection(self.langchoice.FindString(initiallang))
        self.Bind(wx.EVT_CHOICE, self.OnLangChange, self.langchoice)
        listsizer.Add(self.langchoice,0,wx.ALIGN_CENTRE|wx.ALL, 5)
        
        
        self.listbox = wx.ListBox(self, -1,size=(150,300), choices=self.GetTemplateNames(), style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.OnListChange, self.listbox)
        listsizer.Add(self.listbox, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.Button(self,wx.ID_ADD)
        addbutton.SetToolTipString(_('Add a New Template'))
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        buttonsizer.Add(addbutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
        self.rembutton = wx.Button(self,wx.ID_DELETE)
        self.rembutton.SetToolTipString(_('Remove the selected Template'))
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.rembutton)
        self.rembutton.Enable(False)
        buttonsizer.Add(self.rembutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
        listsizer.Add(buttonsizer, 0, wx.ALIGN_CENTRE|wx.ALL, 2)
        
        basesizer.Add(listsizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        
        #right side of panel to display the selected template
        templateinfo = wx.BoxSizer(wx.VERTICAL)
        
        namesizer = wx.BoxSizer(wx.HORIZONTAL)
        helplabel = wx.StaticText(self, -1, _("Name:"))
        namesizer.Add(helplabel,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        self.nametxt = wx.TextCtrl(self,-1)
        namesizer.Add(self.nametxt,1,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(namesizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        self.nametxt.Enable(False)
        
        helpsizer = wx.BoxSizer(wx.HORIZONTAL)
        helplabel = wx.StaticText(self, -1, _("Help Text:"))
        helpsizer.Add(helplabel,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        self.helptxt = wx.TextCtrl(self,-1)
        helpsizer.Add(self.helptxt,1,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(helpsizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        self.helptxt.Enable(False)
        
        indsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.indentcb = wx.CheckBox(self,label=_("Obey Indentation?"))
        self.indentcb.SetToolTipString(_('Check to have all lines of the template be indented to match the indentation at which the template is inserted'))
        indsizer.Add(self.indentcb,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(indsizer, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        self.indentcb.Enable(False)
        
        templabel = wx.StaticText(self, -1, _('Template Codes:\n')+
                '"${same}": '+_('Replace with selected text.\n"')+
                '${upper}":'+_('Replace with selected, first character upper case.\n')+
                '"${lower}":'+_('Replace with selected, first character lower case.\n')+
                '"$$":'+_('An "$" character.')+'\n'+
                '"#CUR":'+_('Move cursor to this location after inserting template.')+'\n'+
                _('tabs will be replaced by the appropriate indent.')
                )
        templateinfo.Add(templabel, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        self.temptxt = wx.TextCtrl(self,-1,size=(400,300),style = wx.TE_MULTILINE)
        templateinfo.Add(self.temptxt, 1, wx.GROW|wx.ALL, 2)
        self.temptxt.Enable(False)
        
        basesizer.Add(templateinfo, 1, wx.GROW|wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizer(basesizer)
        basesizer.Fit(self)
        
    def GetLangTemplateDict(self,lastlangstr=False):
        if lastlangstr:
            return self.plugin.templates[synglob.GetIdFromDescription(self.lastlangstr)]
        else:
            return self.plugin.templates[synglob.GetIdFromDescription(self.langchoice.GetStringSelection())]
        
    def GetTemplateNames(self):
        return self.GetLangTemplateDict().keys()
    
    def UpdateTemplateinfoUI(self,name):
        try:
            templ = self.GetLangTemplateDict()[name]
        except KeyError:
            templ = None
            
        if templ is None:
            #starts out blank
            self.nametxt.SetValue(str(name) if name is not None else '')
            self.temptxt.SetValue('')
            self.helptxt.SetValue('')
            self.indentcb.SetValue(False)
        else:
            self.nametxt.SetValue(templ.name)
            self.temptxt.SetValue(templ.templ.template)
            self.helptxt.SetValue(templ.description)
            self.indentcb.SetValue(templ.indent)
            
        enabled = name is not None
        self.nametxt.Enable(enabled)
        self.temptxt.Enable(enabled)
        self.helptxt.Enable(enabled)
        self.indentcb.Enable(enabled)
            
        self.lastname = name
            
    def ApplyTemplateInfo(self,updatelistind=None,lastlangstr=False):
        name = self.nametxt.GetValue()
        if name.startswith('<') or name.endswith('>') or name.strip()=='':
            return #don't apply initial names
        
        help = self.helptxt.GetValue()
        tempstr = self.temptxt.GetValue()
        obeyind = self.indentcb.GetValue()
        
        ct = CodeTemplate(name,tempstr,help,obeyind)
        templates = self.GetLangTemplateDict(lastlangstr)
        templates[name] = ct
        
        if name != self.lastname:
            if self.lastname in templates:
                del templates[self.lastname]
            self.lastname = name
        
        if updatelistind is not None:
            self.listbox.SetString(updatelistind,name)
        
            
    def OnAdd(self,evt):
        ntstr = '<'+_('New Template')
        i = 1
        for s in self.listbox.GetStrings():
            if s.startswith(ntstr):
                i+=1
        self.listbox.Append(ntstr+'%i>'%i)
    
    def OnRemove(self,evt):
        self.removing = True
        name = self.listbox.GetStringSelection()
        self.listbox.Delete(self.listbox.GetSelection())
        try:
            del self.GetLangTemplateDict()[name]
        except KeyError:
            pass #ignore removal of non-existant template
        self.lastind = None
        self.UpdateTemplateinfoUI(None)
        self.removing = False
        
    def OnListChange(self,evt):
        if not self.removing:
            self.ApplyTemplateInfo(updatelistind=self.lastind)
        self.UpdateTemplateinfoUI(evt.GetString())
        self.lastind = evt.GetSelection()
        self.rembutton.Enable(evt.GetSelection() != -1)
        
    def OnLangChange(self,evt):
        self.ApplyTemplateInfo(lastlangstr=True)
        self.listbox.SetItems(self.GetTemplateNames())
        self.plugin._log('[codetemplater][info]setting %s to %s'%(self.lastlangstr,self.langchoice.GetStringSelection()))
        self.UpdateTemplateinfoUI(None) 
        self.plugin.currentlang = synglob.GetIdFromDescription(self.langchoice.GetStringSelection())
        self.lastlangstr = self.langchoice.GetStringSelection()

def get_language_list():
    #ids = [v[0] for v in synglob.LANG_MAP.values()]
    ids = syntax.SyntaxIds()
    names = [synglob.GetDescriptionFromId(id) for id in ids]
    names.sort()
    return names
        
def load_templates():
    """
    returns a dictionary mapping template names to template objects for the
    requested lexer type 
    """
    from collections import defaultdict
    
    wx.GetApp().GetLog()('[codetemplater][info]hetting %s'%PROFILE_KEY_TEMPLATES)      
    temps = Profile_Get(PROFILE_KEY_TEMPLATES)
    
    templd = defaultdict(lambda:dict())
    try:
        if temps is None:
            dct = load_default_templates()
            #default templates have text name keys instead of IDs like the plugin wants
            
            for k,v in dct.iteritems():
                templd[synglob.GetIdFromDescription(k)] = v
        else:
            #saved templates store the dict instead of objcets, and use language names instead of IDs
            for langname,ld in temps.iteritems():
                newld = {}
                for tempname,d in ld.iteritems():
                    wx.GetApp().GetLog()('[codetemplater][info]dkeys %s'%d.keys())
                    wx.GetApp().GetLog()('[codetemplater][info]dname %s'%d['name'])
                    wx.GetApp().GetLog()('[codetemplater][info]templ %s'%d['templ'])
                    wx.GetApp().GetLog()('[codetemplater][info]description %s'%d['description'])
                    wx.GetApp().GetLog()('[codetemplater][info]indent %s'%d['indent'])
                    newld[tempname] = CodeTemplate(d['name'],d['templ'],
                                                   d['description'],d['indent'])
                templd[synglob.GetIdFromDescription(langname)] = newld
                
        return templd
    except:
        Profile_Del(PROFILE_KEY_TEMPLATES)
        raise
#        if len(temps)>0 and not isinstance(temps.values()[0],CodeTemplate):
#            dct = temps
#        else:
#            #if values are templates, assume we're loading an old version of the
#            #profile where all the values are python templates
#            dct = {'python':temps}
    
#    #saved profile/default has text name keys instead of IDs like the plugin wants
#    dd = defaultdict(lambda:dict())
#    for k,v in dct.iteritems():
#        dd[synglob.GetIdFromDescription(k)] = v
#    return dd

def load_default_templates():
    """
    loads the default set of templates (as a defaultdict) 
    """
    pytemps = []
    proptemp = """
def _get${upper}(self):
\t#CUR
def _set${upper}(self,val):
\traise NotImplementedError
${same} = property(_get${upper},_set${upper},doc=None)
"""[1:] #remove first EOL
    pytemps.append(CodeTemplate('Property',proptemp,_('Convert Selection to Get/Set Property'),True))
    
    delproptemp = """
def _get${upper}(self):
\t#CUR
def _set${upper}(self,val):
\traise NotImplementedError
def _del${upper}(self):
\traise NotImplementedError
${same} = property(_get${upper},_set${upper},_del${upper},doc=None)
"""[1:] #remove first EOL
    pytemps.append(CodeTemplate('DelProperty',delproptemp,_('Convert Selection to Get/Set/Del Property'),True))
    
    getproptemp = """
@property
def ${same}(self):
\t#CUR
"""[1:] #remove first EOL
    pytemps.append(CodeTemplate('ROProperty',getproptemp,_('Convert Selection to read-only Property'),True))
    
    iteritemstemp = """
for k,v in ${same}.iteritems():
\t#CUR
"""[1:] #remove first EOL
    pytemps.append(CodeTemplate('Iterdict',iteritemstemp,_('Iterate over items of selected dictionary'),True))
    
    methodtemp = """
def ${same}(self):
\t#CUR
"""[1:] #remove first EOL
    pytemps.append(CodeTemplate('Method',methodtemp,_('Convert selection into a method'),True))
    
    nietemp = 'raise NotImplementedError'
    pytemps.append(CodeTemplate('NotImplementedError',nietemp,u'',True))
    
    pytemps = dict([(t.name,t) for t in pytemps])
    
    return {'python':pytemps}
