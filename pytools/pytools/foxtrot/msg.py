###############################################################################
# Encoding: UTF-8                                                             #
# Name: msg.py                                                                #                                       
# Description: Define class-message                                           #                                       
# Author: Alexey Zankevich <alex.zankevich@gmail.com>                         #                                      
# Copyright: (c) 2009 Alexei Zankevich <alex.zankevich@gmail.com>             #                                      
# Licence: GNU Lesser General Public License v3                               #
############################################################################### 
__version__ = "0.1"
__author__ = "Alexey Zankevich <alex.zankevich@gmail.com>"
__copyright__ = "Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>"
__license__ = "LGPLv3"


class Msg:
    msgtype = 'basic'
    def __init__(self, lineno, msg, **kwargs):
        self.lineno = lineno
        self.msg = msg
    
    def __repr__(self):
        return '<lineno: %s - %s>' %(self.lineno, self.msg)
    

class UndefinedVarMsg(Msg):
    msgtype = 'undefined_var'
    def __init__(self, lineno, msg, **kwargs):
        self.lineno = lineno
        self.msg = msg
        self.varname = kwargs.get('varname', '')
        
   
