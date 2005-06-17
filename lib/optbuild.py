#!/usr/bin/env python
from __future__ import division

__version__ = "$Revision: 1.17 $"

import new
import optparse
import subprocess
from subprocess import PIPE
import sys

from autolog import autolog

_log = autolog()
_log_exec = _log[".exec"]

def _write_log_exec(cmdline):
    if " " in "".join(cmdline):
        _log_exec.info(" ".join("'%s'" % arg.encode("string_escape")
                                for arg in cmdline))
    else:
        _log_exec.info(" ".join(cmdline))

class ReturncodeError(RuntimeError):
    def __init__(self, cmdline, returncode, output=None, error=None):
        self.cmdline = cmdline
        self.returncode = returncode
        self.output = output
        self.error = error

    def __str__(self):
        return "%s returned %s" % (self.cmdline[0], self.returncode)

class Stdin(object):
    """
    indicate that an "argument" is actually input
    """
    def __init__(self, data):
        self.data = data

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

    def build_args(self, args=(), options={}):
        return self._build_options(options) + list(args)

    def build_cmdline(self, args=(), options={}, prog=None):
        if prog is None:
            prog = self.prog
            
        res = [prog]
        res.extend(self.build_args(args, options))

        _write_log_exec(res)
        return res

    def _popen(self, args, options, input=None,
               stdin=None, stdout=None, stderr=None):
        cmdline = self.build_cmdline(args, options)
        pipe = subprocess.Popen(cmdline,
                                stdin=stdin, stdout=stdout, stderr=stderr)
        output, error = pipe.communicate(input)

        returncode = pipe.wait()
        if returncode:
            raise ReturncodeError, (cmdline, returncode,
                                    output, error)

        res = []
        if stdout == PIPE:
            res.append(output)
        if stderr == PIPE:
            res.append(error)

        if len(res) == 1:
            return res[0]
        else:
            return tuple(res)

    def _getoutput(self, args, options, stdout=None, stderr=None):
        input = None
        stdin = None

        try:
            if isinstance(args[0], Stdin):
                if isinstance(args[0].data, basestring):
                    input = args[0].data
                    stdin = PIPE
                elif isinstance(args[0].data, file):
                    stdin = args[0].data
                else:
                    raise ValueError, \
                          "Stdin arg does not contain basestring or file"
                    
                args = args[1:]
        except IndexError:
            pass
            
        return self._popen(args, options, input, stdin, stdout, stderr)

    def getoutput_error(self, *args, **kwargs):
        """
        runs a program and gets the stdout and error
        """
        return self._getoutput(args, kwargs, stdout=PIPE, stderr=PIPE)

    def getoutput(self, *args, **kwargs):
        """
        runs a program and gets the stdout
        """
        return self._getoutput(args, kwargs, stdout=PIPE)

    def run(self, *args, **kwargs):
        """
        runs a program and ignores the stdout
        """
        self._getoutput(args, kwargs)
        return None

    def popen(self, *args, **kwargs):
        """
        spawns a program and doesn't wait for it to return
        """
        cmdline = self.build_cmdline(args, kwargs)

        return subprocess.Popen(cmdline)

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
    def build_args(self, args=(), options={}):
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
