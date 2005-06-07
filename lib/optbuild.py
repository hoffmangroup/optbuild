#!/usr/bin/env python
from __future__ import division

__version__ = "$Revision: 1.5 $"

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
        return self.build_option(self.convert_option_name(option), value)

    def _build_options(self, options):
        # XXX: use the option_list to check/convert the options

        return [self._build_option(*option_item)
                for option_item in options.iteritems()]

    @staticmethod
    def build_option(option, value):
        if value is True:
            return ["--%s" % option]
        elif value is False or value is None:
            return []
        else:
            return ["--%s=%s" % (option, value)]

    def build_args(self, options={}, args=[]):
        return self._build_options(options) + args

    def build_cmdline(self, options={}, args=[], prog=None):
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

class AddableMixin(object):
    __metaclass__ = AddableMixinMetaclass

class Mixin_ArgsFirst(AddableMixin):
    def build_args(self, options={}, args=[]):
        return args + self._build_options(options)

def main(args):
    pass

def _test(*args, **keywds):
    import doctest
    doctest.testmod(sys.modules[__name__], *args, **keywds)

if __name__ == "__main__":
    if __debug__:
        _test()
    sys.exit(main(sys.argv[1:]))
