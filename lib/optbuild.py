#!/usr/bin/env python
from __future__ import division

from __future__ import absolute_import
from __future__ import print_function
import six
__version__ = "$Revision: 1.30 $"

from distutils.spawn import find_executable
from functools import partial
import optparse
import signal
from subprocess import Popen, PIPE
import sys

from autolog import autolog

_log = autolog()
_log_exec = _log[".exec"]

# XXX: we should eliminate dependencies on optparse, I don't think it
# gets us anything


def _write_log_exec(cmdline):
    cmdline_strings = [arg for arg in cmdline if isinstance(arg, six.string_types)]

    if " " in "".join(cmdline_strings):
        # quote every arg
        _log_exec.info(" ".join("'%s'" % arg.encode("unicode_escape")
                                for arg in cmdline_strings))
    else:
        _log_exec.info(" ".join(cmdline_strings))


# XXX: should probably be deprecated in favor of subprocess.CalledProcessError
class ReturncodeError(Exception):
    ## this doesn't have an errno, so it can't be an OSError
    def __init__(self, cmdline, returncode, output=None, error=None):
        self.cmdline = cmdline
        self.returncode = returncode
        self.output = output
        self.error = error

    def __str__(self):
        return "%s returned %s" % (self.cmdline[0], self.returncode)


class SignalError(ReturncodeError):
    def __str__(self):
        try:
            signal_text = _signals[-self.returncode]
        except KeyError:
            signal_text = "signal %d" % -self.returncode

        return "%s terminated by %s" % (self.cmdline[0], signal_text)


def _returncode_error_factory(cmdline, returncode, output=None, error=None):
    if returncode >= 0:
        error_cls = ReturncodeError
    else:
        error_cls = SignalError

    raise error_cls(cmdline, returncode, output, error)


class Stdin(object):
    """
    indicate that an "argument" is actually input
    """
    def __init__(self, data):
        self.data = data


class Cwd(str):
    """
    indicate that an "argument" is a directory to change to
    """
    pass


class OptionBuilder(optparse.OptionParser):
    """
    GNU long-args style option builder
    """
    def __init__(self, prog=None, *args, **kwargs):
        optparse.OptionParser.__init__(self, prog=prog, *args, **kwargs)
        self.dry_run = False

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __str__(self):
        return self.prog

    def __repr__(self):
        return "%s('%s')" % (self.__class__, str(self).encode("string_escape"))

    @staticmethod
    def convert_option_name(option):
        return option.replace("_", "-")

    def _build_option(self, option, value):
        """always returns a list"""
        option = self.convert_option_name(option)

        if not isinstance(value, list):
            value = [value]

        res = []
        for value_item in value:
            res.extend(self.build_option(option, value_item))

        return res

    def _build_options(self, options):
        # XXX: use the option_list to check/convert the options

        # can't use a listcomp because _build_option always returns a
        # list and the empty ones have to be eaten somehow

        res = []
        for key in options:
            res.extend(self._build_option(key, options[key]))
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

    def get_prog(self, prog):
        """
        virtual function to be overriden
        """
        if prog is None:
            prog = self.prog

        return prog

    def build_cmdline(self, args=(), options={}, prog=None):
        res = [self.get_prog(prog)]
        res.extend(self.build_args(args, options))

        _write_log_exec(res)
        return res

    def _popen(self, args, options, input=None,
               stdin=None, stdout=None, stderr=None, cwd=None):
        cmdline = self.build_cmdline(args, options)

        if self.dry_run:
            if cwd or input:
                # XXX: print "cd %s" or use a here document
                raise NotImplementedError

            print((" ".join(cmdline)))
            return

        pipe = Popen(cmdline, stdin=stdin, stdout=stdout, stderr=stderr,
                     cwd=cwd)
        output, error = pipe.communicate(input)

        returncode = pipe.wait()
        if returncode:
            _returncode_error_factory(cmdline, returncode, output, error)

        res = []
        if stdout == PIPE:
            res.append(output)
        if stderr == PIPE:
            res.append(error)

        # if there's only one of (output, error), then only return it
        if len(res) == 1:
            return res[0]
        else:
            # otherwise return a tuple of both
            return tuple(res)

    def _getoutput(self, args, options, stdout=None, stderr=None):
        input = None
        stdin = None
        cwd = None

        arg_list = []
        for arg in args:
            if isinstance(arg, Stdin):
                if isinstance(arg.data, six.string_types):
                    input = arg.data
                    stdin = PIPE
                elif isinstance(arg.data, file):
                    stdin = arg.data
                else:
                    raise ValueError("Stdin arg does not contain basestring"
                                     " or file")
            elif isinstance(arg, Cwd):
                cwd = arg
            else:
                arg_list.append(arg)

        return self._popen(tuple(arg_list), options, input,
                           stdin, stdout, stderr, cwd)

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

        return Popen(cmdline)


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


class OptionBuilder_ShortOptWithEquals(OptionBuilder):
    @staticmethod
    def build_option(option, value):
        if value is True:
            return ["-%s" % option]
        elif value is False or value is None:
            return []
        else:
            return ["-%s=%s" % (option, str(value))]


class OptionBuilder_ShortOptWithSpace_TF(OptionBuilder_ShortOptWithSpace):
    # XXX: this should be an AddableMixin instead

    @staticmethod
    def build_option(option, value):
        parent_build_option = \
            partial(OptionBuilder_ShortOptWithSpace.build_option, option)

        if value is True:
            return parent_build_option("T")
        elif value is False:
            return parent_build_option("F")
        else:
            return parent_build_option(value)


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
        return type(name, (cls, other), {})

    __radd__ = __add__

    def __repr__(cls):
        if cls.__name__.startswith("("):
            # eliminates the __module__ part
            return "<class '%s'>" % cls.__name__
        else:
            return type.__repr__(cls)


def _id(obj):
    # found on python-dev somewhere to get around negative id()
    return (sys.maxsize * 2 + 1) & id(obj)


class AddableMixin(six.with_metaclass(AddableMixinMetaclass, object)):
    def __repr__(self):
        if self.__class__.__name__.startswith("("):
            return "<%s object at 0x%x>" % (self.__class__.__name__, _id(self))
        else:
            return super(AddableMixin, self).__repr__(self)

    def __new__(cls, *args, **kwargs):
        # beginning in Python 2.6, object.__new__ no longer takes
        # args, and raises a deprecation warning, so we strip out any
        # args and kwargs (technically OK) before continuing on
        new = super(AddableMixin, cls).__new__

        if new == object.__new__:
            return new(cls)
        else:
            return new(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        # different depending on whether old- and new-style classes
        # are being mixed, because object.__init__() does not call the
        # next method. It does not cooperate with super() by lack of
        # design. I think this is a bug, but I'm sure the Python core
        # developers wouldn't

        # if this mixing with a new-style class
        if type(self).mro()[-1] is object:
            supertype = AddableMixin
        else:
            # for old-style classes, object goes in the middle
            supertype = object

        init_unbound = super(supertype, type(self)).__init__
        init_bound = super(supertype, self).__init__

        # see comment for AddableMixin.__new__
        if init_unbound == object.__init__:
            return init_bound()
        else:
            return init_bound(*args, **kwargs)


class Mixin_ArgsFirst(AddableMixin):
    def build_args(self, args=(), options={}):
        return list(args) + self._build_options(options)


class Mixin_NoConvertUnderscore(AddableMixin):
    @staticmethod
    def convert_option_name(option):
        return option


class Mixin_UseFullProgPath(AddableMixin):
    def get_prog(self, prog):
        prog = OptionBuilder.get_prog(self, prog)

        res = find_executable(prog)

        if res is None:
            raise IOError("can't find %s in path" % prog)

        return res


def _setup_signals():
    res = {}
    for key, value in six.iteritems(vars(signal)):
        if key.startswith("SIG") and key[4] != "_":
            res[value] = key

    return res

_signals = _setup_signals()


def main(args):
    pass


def _test(*args, **keywds):
    import doctest
    doctest.testmod(sys.modules[__name__], *args, **keywds)

if __name__ == "__main__":
    if __debug__:
        _test()
    sys.exit(main(sys.argv[1:]))
