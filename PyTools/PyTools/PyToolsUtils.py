import os.path

def get_packageroot(filepath):
    # traverse downwards until we are out of a python package
    fullPath = os.path.abspath(filepath)
    parentPath, childPath = os.path.dirname(fullPath), os.path.basename(fullPath)

    while parentPath != "/" and os.path.exists(os.path.join(parentPath, '__init__.py')):
        childPath = os.path.join(os.path.basename(parentPath), childPath)
        parentPath = os.path.dirname(parentPath)
    return (childPath, parentPath)

def get_modulepath(childPath):
    return os.path.splitext(childPath)[0].replace(os.path.sep, ".")