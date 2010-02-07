import wx                   
import iface
import plugin
from os import path
from string import Template

from ed_glob import CONFIG,SB_INFO,ID_RELOAD_ENC
from ed_menu import EdMenu
from syntax import synglob
from profiler import Profile_Get, Profile_Set
_ = wx.GetTranslation

ID_SAVE_TO_PROF = wx.NewId()

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
            
        #pre = wx.PreDialog()
        #pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        #pre.Create(parent, ID, title, pos, size, style)
        #self.PostCreate(pre)
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        
        basesizer = wx.BoxSizer(wx.VERTICAL)
        
        self.edpanel = TemplateEditorPanel(self,plugin,initiallang,-1)
        basesizer.Add(self.edpanel,0)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        basesizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)
        
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        okbtn = wx.Button(self, wx.ID_OK)
        okbtn.SetDefault()
        btnsizer.Add(okbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        profbtn = wx.Button(self, ID_SAVE_TO_PROF,_('Save to Profile'))
        profbtn.SetToolTipString(_('Save to the Profile to be reloaded on next Startup'))
        profbtn.Bind(wx.EVT_BUTTON, self.OnSaveProfile)
        btnsizer.Add(profbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        resetbtn = wx.Button(self, ID_SAVE_TO_PROF,_('Reset to defaults'))
        resetbtn.SetToolTipString(_('Resets the Profile to default as well as the Current Setup'))
        resetbtn.Bind(wx.EVT_BUTTON, self.OnResetProfile)
        btnsizer.Add(resetbtn, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        basesizer.Add(btnsizer,0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(basesizer)
        basesizer.Fit(self)
    
    def OnSaveProfile(self,reset=False):
        tempd = self.edpanel.plugin.templates
        #profile key should be in language name
        d = dict([(synglob.GetDescriptionFromId(k),v) for k,v in tempd.iteritems()])
        Profile_Set(PROFILE_KEY_TEMPLATES,d)
    
    def OnResetProfile(self,evt):
        Profile_Set(PROFILE_KEY_TEMPLATES,None)
        self.edpanel.plugin.templates = load_templates()
        self.edpanel.listbox.SetItems(self.edpanel.GetTemplateNames())
        
        
        
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
        
        self.langcombo = wx.ComboBox(self, -1, initiallang, #size=(150,30),
                                     choices=langchoices,style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX, self.OnLangChange, self.langcombo)
        listsizer.Add(self.langcombo,0,wx.ALIGN_CENTRE|wx.ALL, 5)
        
        
        self.listbox = wx.ListBox(self, -1,size=(150,300), choices=self.GetTemplateNames(), style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX, self.OnListChange, self.listbox)
        listsizer.Add(self.listbox, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        addbutton = wx.Button(self,wx.ID_ADD)
        addbutton.SetToolTipString(_('Add a New Template'))
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        buttonsizer.Add(addbutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
        rembutton = wx.Button(self,wx.ID_DELETE)
        rembutton.SetToolTipString(_('Remove the selected Template'))
        self.Bind(wx.EVT_BUTTON, self.OnRemove, rembutton)
        buttonsizer.Add(rembutton,1,wx.ALIGN_CENTRE|wx.ALL, 5)
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
        
        helpsizer = wx.BoxSizer(wx.HORIZONTAL)
        helplabel = wx.StaticText(self, -1, _("Help Text:"))
        helpsizer.Add(helplabel,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        self.helptxt = wx.TextCtrl(self,-1)
        helpsizer.Add(self.helptxt,1,wx.GROW|wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(helpsizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        
        indsizer = wx.BoxSizer(wx.HORIZONTAL)
        indlabel = wx.StaticText(self, -1, _("Obey Indentation?"))
        indsizer.Add(indlabel,0,wx.ALIGN_CENTER|wx.ALL, 2)
        self.indentcb = wx.CheckBox(self)
        indsizer.Add(self.indentcb,0,wx.ALIGN_CENTRE|wx.ALL, 2)
        templateinfo.Add(indsizer, 0, wx.ALIGN_CENTER|wx.ALL, 2)
        
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
        
        basesizer.Add(templateinfo, 1, wx.GROW|wx.ALIGN_CENTER|wx.ALL, 5)
        
        self.SetSizer(basesizer)
        basesizer.Fit(self)
        
    def GetLangTemplateDict(self,lastlangstr=False):
        if lastlangstr:
            return self.plugin.templates[synglob.GetIdFromDescription(self.lastlangstr)]
        else:
            return self.plugin.templates[synglob.GetIdFromDescription(self.langcombo.GetValue())]
        
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
        items = self.listbox.Append('<'+_('New Template')+'>')
    
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
        
    def OnLangChange(self,evt):
        self.ApplyTemplateInfo(lastlangstr=True)
        self.UpdateTemplateinfoUI(None)
        self.listbox.SetItems(self.GetTemplateNames())
        self.plugin._log('[codetemplater][info]setting %s to %s'%(self.lastlangstr,self.langcombo.GetValue()))
        self.plugin.currentlang = synglob.GetIdFromDescription(self.langcombo.GetValue())
        self.lastlangstr = self.langcombo.GetValue()

def get_language_list():
    ids = [v[0] for v in synglob.LANG_MAP.values()]
    names = [synglob.GetDescriptionFromId(id) for id in ids]
    names.sort()
    return names
        
def load_templates():
    """
    returns a dictionary mapping template names to template objects for the
    requested lexer type 
    """
    from collections import defaultdict
    
    
    temps = Profile_Get(PROFILE_KEY_TEMPLATES)
    if temps is None:
        dct = load_default_templates()
    else:
        if len(temps)>0 and not isinstance(temps.values()[0],CodeTemplate):
            dct = temps
        else:
            #if values are templates, assume we're loading an old version of the
            #profile where all the values are python templates
            dct = {'python':temps}
    
    #saved profile/default has text name keys instead of IDs like the plugin wants
    dd = defaultdict(lambda:dict())
    for k,v in dct.iteritems():
        dd[synglob.GetIdFromDescription(k)] = v
    return dd

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
