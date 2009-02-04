###############################################################################
# Encoding: UTF-8                                                             #
# Name: __init__.py                                                           #                                       
# Description: Main module for Foxtrot package                                #                                       
# Author: Alexey Zankevich <alex.zankevich@gmail.com>                         #                                      
# Copyright: (c) 2009 Alexei Zankevich <alex.zankevich@gmail.com>             #                                      
# Licence: GNU Lesser General Public License v3                               #
############################################################################### 
__version__ = "0.1"
__author__ = "Alexey Zankevich <alex.zankevich@gmail.com>"
__copyright__ = "Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>"
__license__ = "LGPLv3"


import compiler

from visitor import CheckVarVisitor
from walker import AstWalker
from msg import Msg


def check_vars(text):
    '''Check undeclared variables in the python source code'''
    try:
        ast = compiler.parse(text)
    except SyntaxError, e:
        return [Msg(e.lineno, e.args[0])]
    visitor = CheckVarVisitor()
    ast_walker = AstWalker(visitor)
    ast_walker.run(ast)
    return visitor.msg_list
