###############################################################################
# Encoding: UTF-8                                                             #
# Name: visitor.py                                                            #                                       
# Description: Define visitors providing code checking functionallity         #
# Author: Alexey Zankevich <alex.zankevich@gmail.com>                         #                                      
# Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>             #                                      
# Licence: GNU Lesser General Public License v3                               #
############################################################################### 
__version__ = "0.1"
__author__ = "Alexey Zankevich <alex.zankevich@gmail.com>"
__copyright__ = "Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>"
__license__ = "LGPLv3"


import __builtin__
from scope import get_ast_name
from msg import UndefinedVarMsg
    

class CheckVarVisitor:
    '''Visitor looks for unused variables in the source code'''
    def __init__(self):
        self.msg_list = []
        self.internal_names = dir(__builtin__)
        self.internal_names.extend(['__file__', '__name__',
                                    '__path__', '_', '__doc__', '__builtins__'])
        self.visit_name_lock = 0
        
    def asquire_name(self):
        self.visit_name_lock += 1
        
    def release_name(self):
        self.visit_name_lock -= 1
        
    def add_msg(self, lineno, msg, **kwargs):
        '''Add msg about the occured error'''
        self.msg_list.append(UndefinedVarMsg(lineno, msg, **kwargs))
        
    def default_visit(self, *args):
        '''Method will be invoked if an appropriate visitNodeName
        method is not found
        '''
        
    def default_leave(self, *args):
        '''Method will be invoked if an appropriate leaveNodeName method is
        not found
        '''
        
    def micro_walk(self, node, **hooks):
        '''Microwalk via the nodes and apply hooks to them.
        The aim of the method is to walk throught some nodes and apply
        node-specific quirks. For example - visitListComp node.
                
        **hooks are keywords like:
            nodename = hook
            
        Where nodename is the node's class name and hook - an arbitrary
        callable
        '''
        nodename = get_ast_name(node)
        if nodename in hooks:
            hooks[nodename](node)
        for child in node.getChildNodes():
            self.micro_walk(child, **hooks)
        
    def visitName(self, node, scope):
        '''Visit a Name node and check if this one is already assigned, add
        error message if it isn't
        '''
        if not self.visit_name_lock:
            self.check_name(node, scope)
    
    def check_name(self, node, scope, *extra_vars):
        '''Check if name is declared'''
        names = self.internal_names + list(extra_vars)
        if node.name not in scope.get_visible_vars():
            if node.name not in names:
                if scope.level > 0:
                    msg = "global name '%s' is not defined" %node.name
                else:
                    msg = "name '%s' is not defined" %node.name
                self.add_msg(node.lineno, msg, varname=node.name)
        else:
            if node.name in scope.get_layer_vars():
                assert not isinstance(scope, int), '%s!' %scope
                if not scope.get_layer_var(node.name).declared(scope,
                                                               node.lineno):
                    if scope.level > 0:
                        msg = "local variable '%s' referenced before "\
                                                    "assignment" %node.name
                    else:
                        msg = "name '%s' is not defined" %node.name
                    self.add_msg(node.lineno, msg, varname=node.name)
            
    def visitAssName(self, node, scope):
        '''Mark that the variable is already assigned'''
        if node.flags == 'OP_ASSIGN':
            scope.get_visible_var(node.name).assign(scope, node.lineno)
        else:
            scope.get_visible_var(node.name).delete(scope, node.lineno)
        
    def visitClass(self, node, outer_scope, scope):
        '''Mark that the variable class_name is already assigned in the outer
        scope's level
        '''
        outer_scope.get_layer_var(node.name).assign(outer_scope, node.lineno)
        
    def visitFunction(self, node, outer_scope, scope):
        '''Mark that the variable function_name is already assigned in the
        outer scope's level. Also set all the function's arguments assigned
        in the current scope
        '''
        outer_scope.get_layer_var(node.name).assign(outer_scope, node.lineno)
        for name in node.argnames:
            var = scope.get_layer_var(name)
            var.assign(scope, node.lineno)
            
    def visitListComp(self, node, scope):
        '''Visit ListComp node and mark all the inner variables as assigned.
        It is neccessarly to do because of the Name node is always visited
        before AssName node in construction like [x for x in my_list if x]
        '''
        self.asquire_name()
        assigned = {}
        def as_hook(asnode):
            '''Hook to save nodes to be assigned'''
            assigned[asnode.name] = asnode
            
        def name_hook(namenode):
            '''Hook to assign saved nodes'''
            if namenode.name in assigned:
                var = scope.get_visible_var(namenode.name)
                var.assign(scope, namenode.lineno)
            self.check_name(namenode, scope)
            
        self.micro_walk(node, AssName = as_hook)
        self.micro_walk(node, Name = name_hook)
    
    def leaveListComp(self, *args):
        '''Say that the Name node will not to be skipped during walking
        the AST
        '''
        self.release_name()
        
    def visitLambda(self, node, scope):
        '''Mark all the lambda's arguments as assigned in its scope'''
        for name in node.argnames:
            var = scope.get_layer_var(name) 
            var.assign(scope, node.lineno)
        
    def visitImport(self, node, scope):
        '''Mark all imported variables as assigned excepted ones
        imported by "*"
        '''
        for name, asname in node.names:
            name = name.strip('.').split('.')[0]
            if asname:
                use_name = asname
            else:
                use_name = name
            if not use_name == '*':
                var = scope.get_visible_var(use_name)
                var.assign(scope, node.lineno)         
        
    def visitFrom(self, node, scope):
        '''Equal to visitImport, so lets simply re-use it'''
        for name, asname in node.names:
            if not node.modname == '__future__':
                self.visitImport(node, scope)
