import sys

# based on: http://blog.yjl.im/2009/02/propery-setter-and-deleter-in-python-25.html
# For Python 2.5-, this will enable the similar property mechanism as in
# Python 2.6+/3.0+. The code is based on
# http://bruynooghe.blogspot.com/2008/04/xsetter-syntax-in-python-25.html
if sys.version_info[:2] <= (2, 5):
    # If you need to access original built-in property(), uncomment the next line.
    # __builtin__._property = property

    import __builtin__
    if not hasattr(__builtin__.property, "setter"):
        class property(__builtin__.property):
            __metaclass__ = type

            def setter(self, method):
                return property(self.fget, method, self.fdel)

            def deleter(self, method):
                return property(self.fget, self.fset, method)

            @__builtin__.property
            def __doc__(self):
                """Doc seems not to be set correctly when subclassing"""
                return self.fget.__doc__

        __builtin__.property = property
