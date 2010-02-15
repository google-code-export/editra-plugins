###############################################################################
# Name: regexcheckui.py                                                       #
# Purpose: RegexCheck plugin                                                  #
# Author: Erik Tollerud <erik.tollerud@gmail.com>                             #
# Copyright: (c) 2010 Erik Tollerud <erik.tollerud@gmail.com>                 #
# License: wxWindows License                                                  #
###############################################################################

"""UI elements for the RegexCheck plugin."""
__author__ = "Erik Tollerud"
__version__ = "0.1"

#-----------------------------------------------------------------------------#

import wx      

_ = wx.GetTranslation

#color sequence from kiki 
COLORS = ["#0000AA", "#00AA00", "#FFAA55", "#AA0000", "#00AAAA", "#AA00AA", 
          "#AAAAAA", "#0000FF", "#00FF00", "#00FFFF", "#FF0000", "#DDDD00", 
          "#FF00FF", "#AAAAFF", "#FF55AA", "#AAFF55", "#FFAAAA", "#55AAFF", 
          "#FFAAFF", "#000077", "#007700", "#770000", "#007777", "#770077", 
          "#777700"]
          
          

class RegexCheckPanel(wx.Panel):
    """The Panel for RegexCheck"""
    
    def __init__(self,parent,*args,**kwargs):
        wx.Panel.__init__(self,parent,*args,**kwargs)
        
        basesizer = wx.BoxSizer(wx.VERTICAL)
        
        topsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        toplabel = wx.StaticText(self, -1, _("Regular Expression:"))
        self.regextextctrl = wx.TextCtrl(self,-1,'')     
        topsizer.Add(toplabel, 0, wx.ALIGN_LEFT|wx.ALL|wx.ALIGN_CENTER_VERTICAL)
        topsizer.Add(self.regextextctrl, 1, wx.ALIGN_LEFT|wx.ALL,border=5)
        basesizer.Add(topsizer, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL)
        
        midsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        testbutton = wx.Button(self,-1,_('Test on Sample'))
        self.matchchoices = wx.Choice(self,-1,choices=[_(u'Findall'),_(u'Search'),_(u'Match')])
        insertbutton = wx.Button(self,-1,_('Insert Expression at Cursor'))
        self.rawcheckbox = wx.CheckBox(self,-1,_('Raw string?'))
        self.rawcheckbox.SetValue(True)
        
        flagsizer = wx.BoxSizer(wx.HORIZONTAL)
        flaglabel = wx.StaticText(self, -1, _("Regex Flags:"))
        flags = [
        'IGNORECASE(I)',
        'LOCALE(L)',
        'MULTILINE(M)',
        'DOTALL(S)',
        'UNICODE(U)',
        'VERBOSE(X)']
        self.flagcheckboxes = [wx.CheckBox(self,-1,f) for f in flags]  
        
        midsizer.Add(testbutton, 0, wx.ALIGN_LEFT|wx.ALL,border=5)
        midsizer.Add(self.matchchoices, 0, wx.ALL|wx.ALIGN_CENTER)
        midsizer.Add(insertbutton, 0, wx.ALIGN_LEFT|wx.ALL,border=5)
        midsizer.Add(self.rawcheckbox, 0, wx.ALL|wx.ALIGN_CENTER)
        midsizer.Add(flaglabel, 0, wx.ALIGN_CENTRE|wx.ALL,border=5)      
        for cb in self.flagcheckboxes:
            midsizer.Add(cb,0,wx.ALIGN_CENTER|wx.ALL)
        basesizer.Add(midsizer, 0, wx.GROW|wx.ALIGN_CENTRE|wx.ALL)
        
        
        
        textsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        textlabel = wx.StaticText(self, -1, _("Sample Text:"))
        self.sampletextctrl = wx.TextCtrl(self,-1,'',style=wx.TE_MULTILINE)
        textsizer.Add(textlabel, 0, wx.ALIGN_CENTRE|wx.ALL)
        textsizer.Add(self.sampletextctrl, 1, wx.GROW|wx.ALIGN_CENTRE|wx.ALL,border=2)
        basesizer.Add(textsizer, 4, wx.GROW|wx.ALIGN_CENTRE|wx.ALL)
        
        bottomsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        outlabel = wx.StaticText(self, -1, _("Output:"))
        self.outputtextctrl = wx.TextCtrl(self,-1,'',style=wx.TE_MULTILINE)
        self.outputtextctrl.SetEditable(False)
        self.outputtextctrl.SetBackgroundColour(outlabel.GetBackgroundColour())
        
        bottomsizer.Add(outlabel, 0, wx.ALIGN_CENTRE|wx.ALL,border=2)
        bottomsizer.Add(self.outputtextctrl, 1,  wx.GROW|wx.ALIGN_CENTRE|wx.ALL,border=2)
        basesizer.Add(bottomsizer, 5, wx.GROW|wx.ALIGN_CENTRE|wx.ALL)
        
        self.SetSizer(basesizer)
        basesizer.Fit(self)
        
        
        self.infobox = None
        
        
        testbutton.Bind(wx.EVT_BUTTON, self.OnTest)
        insertbutton.Bind(wx.EVT_BUTTON, self.OnInsert)
        
    def GetFormattedRegex(self):
        text = self.regextextctrl.GetValue()
        if self.rawcheckbox.GetValue():
            text = "r'%s'"%text
        else:
            text = "'%s'"%text.replace('\\','\\\\')
        return text
        
    def OnTest(self,evt):
        import re
        retext = self.regextextctrl.GetValue()
        wx.GetApp().GetLog()('[regexcheck][info]trying re '+retext)
        
        flags = 0
        for cb in self.flagcheckboxes:
            if cb.GetValue():
                flagname = cb.GetLabel().split('(')[0].strip()
                flagval = getattr(re,flagname)
                flags = flags|flagval
        wx.GetApp().GetLog()('[regexcheck][info]re flags '+str(flags))
        if retext.strip() == '':
            self.outputtextctrl.SetValue(_(u'No regex Entered'))
        else:
            try:
                matchtext = self.sampletextctrl.GetValue()
                sel = self.matchchoices.GetSelection()
                if sel == 0: #find all
                    matchlocs = []
                    for m in re.finditer(retext,matchtext,flags):
                        matchlocs.extend(self.FindMatchGroups(m,matchtext[m.start():m.end()]))
                    self.ApplyOutput(matchlocs,matchtext)
                else:
                    if sel == 1: #search
                        match = re.search(retext,matchtext,flags)
                    else: #match
                        assert sel==2,'invalid choice option index %i'%sel
                        match = re.match(retext,matchtext,flags)
                    if match is None:
                        matchlocs = []
                    else:
                        matchlocs = self.FindMatchGroups(match,matchtext)
                    self.ApplyOutput(matchlocs,matchtext)
                        
            except re.error,e:
                self.outputtextctrl.SetValue(_(u'Regex compilation error: %s'%e.args))
                
    def FindMatchGroups(self,matchobj,text):
        """
        returns a sequence of tuples of (groupname,groupstartind,groupendind)
        """
        grps = []
        grps.append(('0',matchobj.start(),matchobj.end()))
        
        #create (grpnum,start,end) sequence
        for i,match in enumerate(matchobj.groups()):
            if match is not None:
                span = matchobj.span(i+1)
                grps.append((str(i+1),span[0],span[1]))
        
        #replace named groups with the correct name
        for k in matchobj.groupdict():
            span = matchobj.span(k)
            for i,(n,s,e) in enumerate(grps):
                if span[0]==s and span[1]==e:
                    break
            else:
                i = None
            if i is not None:
                grps[i] = (k,s,e)
        
        return grps
    def ApplyOutput(self,matchlocs,matchtext):
        import operator
        
        if len(matchlocs)==0:
            self.outputtextctrl.SetValue(_(u'No matches'))
        else:
            indstrs = []
            colori = 0
            for name,start,end in matchlocs[::-1]:
                indstrs.append((start,'(',colori))
                indstrs.append((end,')'+name,colori))
                colori += 1
            indstrs.sort(key=operator.itemgetter(0))
            
            curri = 0
            strlist = []
            colors = []
            for ind,nm,color in indstrs:
                strlist.append(matchtext[curri:ind])
                colors.append(None)
                strlist.append(nm)
                colors.append(color)
                curri = ind
            #flip colors order to be forward again
            maxc = max(colors)
            colors = [None if c is None else maxc-c for c in colors]
                
            strlist.append(matchtext[curri:])
            self.outputtextctrl.SetValue(''.join(strlist))
            
            curri = 0
            oldfont = self.outputtextctrl.GetFont()
            biggerfont = wx.Font(
                    oldfont.GetPointSize()+3,
                    oldfont.GetFamily(),
                    oldfont.GetStyle(),
                    oldfont.GetWeight())
            smallerfont = wx.Font(
                    oldfont.GetPointSize()-3,
                    oldfont.GetFamily(),
                    oldfont.GetStyle(),
                    oldfont.GetWeight())
            for substr,color in zip(strlist,colors):
                if color is not None:
                    self.outputtextctrl.SetStyle(curri,curri+1,wx.TextAttr(self.ColorCycle(color),wx.NullColour, biggerfont))
                    if len(substr)>1:
                        self.outputtextctrl.SetStyle(curri+1,curri+len(substr),wx.TextAttr(self.ColorCycle(color),wx.NullColour, smallerfont))
                curri += len(substr)
                
    def ColorCycle(self,colori):
        return COLORS[colori%len(COLORS)]
    
    def OnInsert(self,evt):
        wx.GetApp().GetLog()('[regexcheck][info]inserting '+retext)
        current_buffer = wx.GetApp().GetCurrentBuffer()
        seltext = current_buffer.GetSelectedText()
        if seltext != '':
            current_buffer.DeleteBack()
        retext = self.GetFormattedRegex()
        if retext.strip() != '':
            current_buffer.AddText(retext)