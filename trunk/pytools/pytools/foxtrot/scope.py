###############################################################################
# Encoding: UTF-8                                                             #
# Name: scope.py                                                              #                                       
# Description: Create nested scopes' classes from AST nodes                   #                                       
# Author: Alexey Zankevich <alex.zankevich@gmail.com>                         #                                      
# Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>             #                                      
# Licence: GNU Lesser General Public License v3                               #
############################################################################### 
__version__ = "0.1"
__author__ = "Alexey Zankevich <alex.zankevich@gmail.com>"
__copyright__ = "Copyright: (c) 2009 Alexey Zankevich <alex.zankevich@gmail.com>"
__license__ = "LGPLv3"



def get_ast_name(node):
    '''Get the node's class name'''
    return node.__class__.__name__
    

class Assign:
    '''Contains information about all the variable's assignments'''
    def __init__(self, scope, lineno):
        self.scope = scope
        self.lineno = lineno
        
    def __repr__(self):
        return '<assign:%s,%s>' %(self.scope.level, self.lineno)
        
        
class Delete(Assign):
    '''Contains information about all the variable's deletes'''
    def __repr__(self):
        return '<delete:%s,%s>' %(self.scope.level, self.lineno)    


class Var:
    '''Class contains minimal information about variable's declaration'''
    def __init__(self, name):
        self.name = name
        self.assigns = []
        self.deletes = []
        
    def assign(self, scope, lineno):
        '''Mark that the variable has just been assigned'''
        a = Assign(scope, lineno)
        self.assigns.append(a)
        
    def delete(self, scope, lineno):
        '''Mark that the variable has just been deleted'''
        d = Delete(scope, lineno)
        self.deletes.append(d)
        
    def declared(self, scope, lineno):
        '''Check if the variable is declared in the current line on the current
        level
        '''
        if self.declared_low_scope(scope):
            return True
        if self.declared_this_scope(scope, lineno):
            return True
        
    def declared_low_scope(self, scope):
        '''Check if the variable is declared on the level lower than current'''
        if self.assigns_low_scope(scope):
            return True
    
    def declared_this_scope(self, scope, lineno):
        '''Check if the variable is available on this level'''
        assigns = self.assigns_this_scope(scope)
        deletes = self.deletes_this_scope(scope)
        a = None
        d = None
        for a in assigns[::-1]:
            if a.lineno <= lineno:
                break
        for d in deletes[::-1]:
            if d.lineno < lineno:
                break
        if a:
            if a.lineno <= lineno:
                if not d:
                    return True
                else:
                    if a.lineno >= d.lineno:
                        return True
                    else:
                        if d.lineno >= lineno:
                            return True
        return False   
    
    def assigns_low_scope(self, scope):
        '''Get all assignments on the level lower than the current'''
        assigns = []
        for a in self.assigns:
            if a.scope.level < scope.level:
                assigns.append(a)
        return assigns
    
    def this_scope_filt(self, scope):
        '''Get a filter to filter assignements and deletes only on the same
        level
        '''
        def filt(arg):
            if scope is arg.scope:
                return True
        return filt
        
    def assigns_this_scope(self, scope):
        '''Get all assignements only on the same level'''
        f = self.this_scope_filt(scope)
        return filter(f, self.assigns)
        
    def deletes_this_scope(self, scope):
        '''Get all deletes only on the same level'''
        f = self.this_scope_filt(scope)
        return filter(f, self.deletes)
        
    def __repr__(self):
        '''Prettyfy variable's representation'''
        return '<var:%s>' %self.name


class VarFactory:
    '''Get new variables' names from nodes below:
    
        Class
        Function
        Import
        From
        AssName
        
    '''
    def get_vars(self, node):
        '''get variables list from the current node'''
        try:
            fun_name = 'from%s' %get_ast_name(node)
            return getattr(self, fun_name)(node)
        except AttributeError:
            return []
    
    def fromClass(self, node):
        return [Var(node.name)]

    def fromFunction(self, node):
        return [Var(node.name)]
    
    def fromFrom(self, node):
        '''Equally as from_import'''
        return self.fromImport(node)
    
    def fromImport(self, node):
        varlist = []
        for name, asname in node.names:
            #assign dotted names as ordinal names
            #for example: import os.path will create variable os
            name = name.strip('.').split('.')[0]
            if asname:
                varlist.append(Var(asname))
            elif not name == '*':
                varlist.append(Var(name))
        return varlist

    def fromAssName(self, node):
        return [Var(node.name)]
        
    
class Scope:
    var_factory = VarFactory()
    def __init__(self, node, root, outer_scope):
        '''node - AST's node from which the scope has to be produced,
        root - root scope
        '''
        self.root = root
        self.scopes = []
        self.vars = {}
        self.force_globs = {}
        self.outers = {}
        self.node = node
        self.outer_scope = outer_scope
        if node:
            self.analyse(node)
    
    def get_inner_visible(self):
        '''Get all variables which have to be visible inside a nested
        scope
        '''
        return self.get_visible_vars()
        
    def set_visible_vars(self, outer_scope):
        '''Set all variables to be visible inside the current scope from
        the outer one
        '''
        self.outers.update(outer_scope.get_inner_visible())
        
    def set_var(self, name, var=None):
        '''Set a variable to the current scope'''
        if not var:
            var = Var(name)
        self.vars[name] = var
            
    def pop_var(self, name):
        '''Remove a variable from the current scope'''
        if name in self.vars:
            self.vars.pop(name)
        
    def analyse(self, node):
        '''Analyse node, create new defined variables and resolve globals
        ones
        '''
        for child in node.getChildNodes():
            ast_name = get_ast_name(child)
            if ast_name in ['Class', 'Function', 'AssName', 'From', 'Import']:
                #a new variable just has been defined
                for var in self.var_factory.get_vars(child):
                    if var.name not in self.force_globs:
                        if var.name not in self.get_layer_vars():
                            self.set_var(var.name, var)
                
            if ast_name == 'Global':
                #the current variable is global
                #all the nested scopes have to update their outer variables
                for name in child.names:
                    self.force_globs[name] = True
                    if name in self.get_layer_vars():
                        self.pop_var(name)
                    if name in self.root.get_layer_vars():
                        var = self.root.get_layer_var(name)
                    else:
                        var = Var(name)
                        self.root.set_var(name, var)
                    self.set_var(name, var)
                    self.root.update_outers()
            
            if ast_name not in ['Class', 'Function', 'Lambda']:
                self.analyse(child)
    
    def get_outer_vars(self):
        '''Get all variables which were passed from the outer scope'''
        return self.outers.copy()
        
    def get_outer_var(self, varname):
        '''Get a variable from the outer scope by its name'''
        return self.get_outer_vars()[varname]
    
    def get_layer_vars(self):
        '''Get all variables defined inside the current scope'''
        return self.vars.copy()

    def get_layer_var(self, varname):
        '''Get a variable defined inside the current scope by its name'''
        return self.get_layer_vars()[varname]
        
    def get_visible_vars(self):
        '''Get all visible variables inside the current scope'''
        dic = self.outers.copy()
        dic.update(self.vars)
        return dic
        
    def get_visible_var(self, varname):
        '''Get a visible variable inside the current scope by variable's name'''
        return self.get_visible_vars()[varname]
        
    def add_scope(self, scope):
        '''Add a nested scope to the current'''
        self.scopes.append(scope)
        
    def update_outers(self):
        '''Update all outer variables recursively inside the whole scopes'
        tree
        '''
        for scope in self.scopes:
            scope.set_visible_vars(self)
        
        
class FunctionScope(Scope):
    def __init__(self, node, root, outer_scope):
        Scope.__init__(self, node, root, outer_scope)
        for arg in node.argnames:
             self.set_var(arg)
        self.level = outer_scope.level + 1


class LambdaScope(Scope):
    def __init__(self, node, root, outer_scope):
        Scope.__init__(self, node, root, outer_scope)
        for arg in node.argnames:
             self.set_var(arg) 
        self.level = outer_scope.level + 1
    
    
class ModuleScope(Scope):
    def __init__(self, node, root):
        Scope.__init__(self, node, root, root)
        self.level = 0


class ClassScope(Scope):
    def __init__(self, node, root, outer_scope):
        Scope.__init__(self, node, root, outer_scope)
        self.level = outer_scope.level
        
    def get_inner_visible(self):
        return self.get_outer_vars()
        
    def get_visible_vars(self):
        '''Remove class itself from visible variables, but only from current
        class's scope
        '''
        dic = self.get_layer_vars()
        dic.update(self.get_outer_vars())
        if self.node.name in dic:
            """
            >>> class A:
            ...     print A #<- class A should not be visible inside
            ...             #   class's definition
            
            But here there is no A inside class B:
            >>> class B:
            ...     class A:
            ...         print A
            
            So, we have to check if variable exist. If yes, remove it
            """
            dic.pop(self.node.name)
        return dic


class DecoratorScope(Scope):
    """Decorator scope is not really a scope, but it modify classes scope, so
    it is not a bad idea to make a pseudo scope
    """
    def __init__(self, node, root, outer_level):
        Scope.__init__(self, node, root)
        self.level = outer_level.level
        
    def set_visible_vars(self, outer_scope):
        '''Set all variables to be visible inside the current scope from
        the outer one
        '''
        self.outers.update(outer_scope.get_visible_vars())
