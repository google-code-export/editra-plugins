###############################################################################
# Encoding: UTF-8                                                             #
# Name: walker.py                                                             #                                       
# Description: Walk through the AST and invoke visitors' visit methods        #                                       
# Author: Alexey Zankevich <alex.zankevich@gmail.com>                         #                                      
# Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>             #                                      
# Licence: GNU Lesser General Public License v3                               #
############################################################################### 
__version__ = "0.1"
__author__ = "Alexey Zankevich <alex.zankevich@gmail.com>"
__copyright__ = "Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>"
__license__ = "LGPLv3"


from scope import ModuleScope, ClassScope, FunctionScope, LambdaScope
from scope import get_ast_name



class AstWalker:
    '''Walk via AST and invoke all the visitors' visitXXX and leaveXXX
    functions
    '''
    scopes = {
        'Function': FunctionScope,
        'Lambda': LambdaScope,
        'Class': ClassScope,
        'Module': ModuleScope
            }
            
    def __init__(self, *visitors):
        self.root = None
        self.visitors = visitors
        
    def scan_scope(self, node, *args):
        '''Scan the scope and return a new Scope instance'''
        name = get_ast_name(node)
        scope_class = self.get_scope_class(name)
        return scope_class(node, *args)
        
    def get_scope_class(self, name):
        return self.scopes[name]
        
    def run(self, ast):
        '''Start the walk process'''
        if get_ast_name(ast) == 'Module':
            self.root = self.scan_scope(ast, None)
        else:
            raise RuntimeError('Root scope can be extracted only from '\
                               'Module node')
        self.visit(ast, self.root)
        self.walk(ast, self.root)
        self.leave(ast, self.root)
            
    def walk(self, node, scope):
        '''Walk nodes recursively, generate dialed nested scopes and invoke
        invoke all the visitors' visitXXX and leaveXXX functions
        ''' 
        name = get_ast_name(node)
        for child in node.getChildNodes():
            child_name = get_ast_name(child)
            if child_name in ('Function', 'Class', 'Lambda'):
                use_scope = self.scan_scope(child, self.root, scope)
                use_scope.set_visible_vars(scope)
                scope.add_scope(use_scope)
            elif child_name == 'Decorators':
                use_scope = scope.outer_scope
            else:
                use_scope = scope
            if child_name in ('Function', 'Class'):
                self.visit(child, scope, use_scope)
                self.walk(child, use_scope)
                self.leave(child, scope, use_scope)
            else:
                self.visit(child, use_scope)
                self.walk(child, use_scope)
                self.leave(child, use_scope)
                
    def visit(self, node, *args):
        '''Invoke all the visitors' visitNodeName functions'''
        for v in self.visitors:
            try:
                getattr(v, 'visit%s' %get_ast_name(node))(node, *args)
            except AttributeError, e:
                v.default_visit(node, *args)
           
    def leave(self, node, *args):
        '''Invoke all the visitors' leaveNodeName functions'''
        for v in self.visitors:
            try:
                getattr(v, 'leave%s' %get_ast_name(node))(node, *args)
            except AttributeError, e:
                v.default_leave(node, *args)
