#!/usr/bin/env python
from __future__ import division

__version__ = "$Revision: 1.7 $"

import new
import optparse
import subprocess
import sys

from autolog import autolog

_log = autolog()
_log_exec = _log[".exec"]

class ReturncodeError(RuntimeError):
    def __init__(self, cmdline, returncode, stdout=None):
        self.cmdline = cmdline
        self.returncode = returncode
        self.stdout = stdout

    def __str__(self):
        return "%s returned %s" % (self.cmdline[0], self.returncode)

class OptionBuilder(optparse.OptionParser):
    """
    GNU long-args style option builder
    """
    @staticmethod
    def convert_option_name(option):
        return option.replace("_", "-")

    def _build_option(self, option, value):
        """always returns a list"""
        return self.build_option(self.convert_option_name(option), value)
    
    def _build_options(self, options):
        # XXX: use the option_list to check/convert the options

        # can't use a listcomp because _build_option always returns a
        # list and the empty ones have to be eaten somehow
        
        res = []
        for option_item in options.iteritems():
            res.extend(self._build_option(*option_item))
        return res
            
    @staticmethod
    def build_option(option, value):
        if value is True:
            return ["--%s" % option]
        elif value is False or value is None:
            return []
        else:
            return ["--%s=%s" % (option, value)]

    def build_args(self, options={}, args=()):
        return self._build_options(options) + list(args)

    def build_cmdline(self, options={}, args=(), prog=None):
        if prog is None:
            prog = self.prog
            
        return [prog] + self.build_args(options, args)

    def getoutput(self, *args, **kwargs):
        """
        runs a program and gets the stdout
        """
        cmdline = self.build_cmdline(kwargs, args)

        _log_exec.info(" ".join(cmdline))
        pipe = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
        res = pipe.communicate()[0]

        returncode = pipe.wait()
        if returncode:
            raise ReturncodeError, (cmdline, returncode, res)

        return res

    def run(self, *args, **kwargs):
        """
        runs a program and ignores the stdout
        """
        cmdline = self.build_cmdline(kwargs, args)

        _log_exec.info(" ".join(cmdline))
        returncode = subprocess.call(cmdline)
        if returncode:
            raise ReturncodeError, (cmdline, returncode)

class OptionBuilder_LongOptWithSpace(OptionBuilder):
    @staticmethod
    def build_option(option, value):
        if value is True:
            return ["--%s" % option]
        elif value is False or value is None:
            return []
        else:
            return ["--%s" % option, str(value)]

class OptionBuilder_ShortOptWithSpace(OptionBuilder):
    @staticmethod
    def build_option(option, value):
        if value is True:
            return ["-%s" % option]
        elif value is False or value is None:
            return []
        else:
            return ["-%s" % option, str(value)]

class OptionBuilder_NoHyphenWithEquals(OptionBuilder):
    @staticmethod
    def build_option(option, value):
        if isinstance(value, bool):
            value = int(value)
        elif value is None:
            return []

        return ["%s=%s" % (option, value)]

class AddableMixinMetaclass(type):
    def __add__(cls, other):
        name = "(%s.%s + %s.%s)" % (cls.__module__, cls.__name__,
                                    other.__module__, other.__name__)
        return new.classobj(name, (cls, other), {})

    __radd__ = __add__

    def __repr__(cls):
        if cls.__name__.startswith("("):
            # eliminates the __module__ part
            return "<class '%s'>" % cls.__name__
        else:
            return type.__repr__(cls)

def _id(obj):
    # found on python-dev somewhere to get around negative id()
    return (sys.maxint * 2 + 1) & id(obj)

class AddableMixin(object):
    __metaclass__ = AddableMixinMetaclass

    def __repr__(self):
        if self.__class__.__name__.startswith("("):
            return "<%s object at 0x%x>" % (self.__class__.__name__, _id(self))
        else:
            return object.__repr__(self)

    def __new__(self, *args, **kwargs):
        return object.__new__(self)

    def __init__(self, *args, **kwargs):
        return super(object, self).__init__(*args, **kwargs)

class Mixin_ArgsFirst(AddableMixin):
    def build_args(self, options={}, args=()):
        return list(args) + self._build_options(options)

def main(args):
    pass

def _test(*args, **keywds):
    import doctest
    doctest.testmod(sys.modules[__name__], *args, **keywds)

if __name__ == "__main__":
    if __debug__:
        _test()
    sys.exit(main(sys.argv[1:]))
