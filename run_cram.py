#!/usr/bin/python

import sys
import cram

import optparse
import os
import shlex
import shutil
import sys
import tempfile

try:
    import configparser
except ImportError: # pragma: nocover
    import ConfigParser as configparser


import os
import sys

from cram._encoding import b, fsdecode, fsencode
from cram._test import testfile

# from cram._cli import runcli
from cram._encoding import b, fsencode, stderrb, stdoutb
from cram._run import _walk, _findtests
# from cram._xunit import runxunits

from cram._main import _which, _expandpath, _OptionParser, _parseopts
from cram._run import * 

######################## _test.py

import itertools
import os
import re
import time

from cram._encoding import b, bchr, bytestype, envencode, unicodetype
from cram._diff import esc, glob, regex, unified_diff
from cram._process import PIPE, STDOUT, execute

__all__ = ['test', 'testfile']

_needescape = re.compile(b(r'[\x00-\x09\x0b-\x1f\x7f-\xff]')).search
_escapesub = re.compile(b(r'[\x00-\x09\x0b-\x1f\\\x7f-\xff]')).sub
_escapemap = dict((bchr(i), b(r'\x%02x' % i)) for i in range(256))
_escapemap.update({b('\\'): b('\\\\'), b('\r'): b(r'\r'), b('\t'): b(r'\t')})

def _escape(s):
    """Like the string-escape codec, but doesn't escape quotes"""

    # print (_escapesub(s, s))
  #  print (_escapesub(lambda m: _escapemap[m.group(0)], s[:-3]) + b(' (esc)\n'))

    return (_escapesub(lambda m: _escapemap[m.group(0)], s[:-1]) + b(' (esc)\n'))

def my_test(lines, shell='/bin/sh', indent=2, testname=None, env=None,
         cleanenv=True, debug=False):
    r"""Run test lines and return input, output, and diff.

    This returns a 3-tuple containing the following:

        (list of lines in test, same list with actual output, diff)

    diff is a generator that yields the diff between the two lists.

    If a test exits with return code 80, the actual output is set to
    None and diff is set to [].

    Note that the TESTSHELL environment variable is available in the
    test (set to the specified shell). However, the TESTDIR and
    TESTFILE environment variables are not available. To run actual
    test files, see testfile().

    Example usage:

    >>> from cram._encoding import b
    >>> refout, postout, diff = test([b('  $ echo hi\n'),
    ...                               b('  [a-z]{2} (re)\n')])
    >>> refout == [b('  $ echo hi\n'), b('  [a-z]{2} (re)\n')]
    True
    >>> postout == [b('  $ echo hi\n'), b('  hi\n')]
    True
    >>> bool(diff)
    False

    lines may also be a single bytes string:

    >>> refout, postout, diff = test(b('  $ echo hi\n  bye\n'))
    >>> refout == [b('  $ echo hi\n'), b('  bye\n')]
    True
    >>> postout == [b('  $ echo hi\n'), b('  hi\n')]
    True
    >>> bool(diff)
    True
    >>> (b('').join(diff) ==
    ...  b('--- \n+++ \n@@ -1,2 +1,2 @@\n   $ echo hi\n-  bye\n+  hi\n'))
    True

    Note that the b() function is internal to Cram. If you're using Python 2,
    use normal string literals instead. If you're using Python 3, use bytes
    literals.

    :param lines: Test input
    :type lines: bytes or collections.Iterable[bytes]
    :param shell: Shell to run test in
    :type shell: bytes or str or list[bytes] or list[str]
    :param indent: Amount of indentation to use for shell commands
    :type indent: int
    :param testname: Optional test file name (used in diff output)
    :type testname: bytes or None
    :param env: Optional environment variables for the test shell
    :type env: dict or None
    :param cleanenv: Whether or not to sanitize the environment
    :type cleanenv: bool
    :param debug: Whether or not to run in debug mode (don't capture stdout)
    :type debug: bool
    :return: Input, output, and diff iterables
    :rtype: (list[bytes], list[bytes], collections.Iterable[bytes])
    """
    indent = b(' ') * indent
    cmdline = indent + b('$ ')
    conline = indent + b('> ')
    usalt = 'CRAM%s' % time.time()
    salt = b(usalt)

    if env is None:
        env = os.environ.copy()

    if cleanenv:
        for s in ('LANG', 'LC_ALL', 'LANGUAGE'):
            env[s] = 'C'
        env['TZ'] = 'GMT'
        env['CDPATH'] = ''
        env['COLUMNS'] = '80'
        env['GREP_OPTIONS'] = ''

    if isinstance(lines, bytestype):
        lines = lines.splitlines(True)

    if isinstance(shell, (bytestype, unicodetype)):
        shell = [shell]
    env['TESTSHELL'] = shell[0]

    if debug:
        stdin = []
        for line in lines:
            if not line.endswith(b('\n')):
                line += b('\n')
            if line.startswith(cmdline):
                stdin.append(line[len(cmdline):])
            elif line.startswith(conline):
                stdin.append(line[len(conline):])

        execute(shell + ['-'], stdin=b('').join(stdin), env=env)
        return ([], [], [])

    after = {}
    refout, postout = [], []
    i = pos = prepos = -1
    stdin = []
    for i, line in enumerate(lines):
        if not line.endswith(b('\n')):
            line += b('\n')
        refout.append(line)
        if line.startswith(cmdline):
            after.setdefault(pos, []).append(line)
            prepos = pos
            pos = i
            stdin.append(b('echo %s %s $?\n' % (usalt, i)))
            stdin.append(line[len(cmdline):])
        elif line.startswith(conline):
            after.setdefault(prepos, []).append(line)
            stdin.append(line[len(conline):])
        elif not line.startswith(indent):
            after.setdefault(pos, []).append(line)
    stdin.append(b('echo %s %s $?\n' % (usalt, i + 1)))

    output, retcode = execute(shell + ['-'], stdin=b('').join(stdin),
                              stdout=PIPE, stderr=STDOUT, env=env)
    if retcode == 80:
        return (refout, None, [])

    pos = -1
    ret = 0
    for i, line in enumerate(output[:-1].splitlines(True)):
        out, cmd = line, None
        if salt in line:
            out, cmd = line.split(salt, 1)

        if out:
            if not out.endswith(b('\n')):
                out += b(' (no-eol)\n')

            if _needescape(out):
                # print(_needescape(out))
                # print (((out)))
                # print ((_escape(out)))
                out = _escape(out)
            postout.append(indent + out)

        if cmd:
            ret = int(cmd.split()[1])
            if ret != 0:
                postout.append(indent + b('[%s]\n' % (ret)))
            postout += after.pop(pos, [])
            pos = int(cmd.split()[0])

    postout += after.pop(pos, [])
    # for r, p in zip(refout, postout):
    #     if (r != p) :
    #         print (r, p)

    if testname:
        diffpath = testname
        errpath = diffpath + b('.err')
    else:
        diffpath = errpath = b('')
    diff = unified_diff(refout, postout, diffpath, errpath,
                        matchers=[esc, glob, regex])
    for firstline in diff:
        # print (list(diff))
        return refout, postout, itertools.chain([firstline], diff)
    return refout, postout, []

def my_testfile(path, shell='/bin/sh', indent=2, env=None, cleanenv=True,
             debug=False, testname=None):
    """Run test at path and return input, output, and diff.

    This returns a 3-tuple containing the following:

        (list of lines in test, same list with actual output, diff)

    diff is a generator that yields the diff between the two lists.

    If a test exits with return code 80, the actual output is set to
    None and diff is set to [].

    Note that the TESTDIR, TESTFILE, and TESTSHELL environment
    variables are available to use in the test.

    :param path: Path to test file
    :type path: bytes or str
    :param shell: Shell to run test in
    :type shell: bytes or str or list[bytes] or list[str]
    :param indent: Amount of indentation to use for shell commands
    :type indent: int
    :param env: Optional environment variables for the test shell
    :type env: dict or None
    :param cleanenv: Whether or not to sanitize the environment
    :type cleanenv: bool
    :param debug: Whether or not to run in debug mode (don't capture stdout)
    :type debug: bool
    :param testname: Optional test file name (used in diff output)
    :type testname: bytes or None
    :return: Input, output, and diff iterables
    :rtype: (list[bytes], list[bytes], collections.Iterable[bytes])
    """
    f = open(path, 'rb')
    try:
        abspath = os.path.abspath(path)
        env = env or os.environ.copy()
        env['TESTDIR'] = envencode(os.path.dirname(abspath))
        env['TESTFILE'] = envencode(os.path.basename(abspath))
        if testname is None: # pragma: nocover
            testname = os.path.basename(abspath)
        return my_test(f, shell, indent=indent, testname=testname, env=env,
                    cleanenv=cleanenv, debug=debug)
    finally:
        f.close()

######################## _run.py

def my_runtests(paths, tmpdir, shell, indent=2, cleanenv=True, debug=False):
    """Run tests and yield results.

    This yields a sequence of 2-tuples containing the following:

        (test path, test function)

    The test function, when called, runs the test in a temporary directory
    and returns a 3-tuple:

        (list of lines in the test, same list with actual output, diff)
    """
    cwd = os.getcwd()
    seen = set()
    basenames = set()
    for i, path in enumerate(_findtests(paths)):
        abspath = os.path.abspath(path)
        if abspath in seen:
            continue
        seen.add(abspath)

        if not os.stat(path).st_size:
            yield (path, lambda: (None, None, None))
            continue

        basename = os.path.basename(path)
        if basename in basenames:
            basename = basename + b('-%s' % i)
        else:
            basenames.add(basename)

        def test():
            """Run test file"""
            testdir = os.path.join(tmpdir, basename)
            os.mkdir(testdir)
            #
            import shutil
            parent_dir = os.path.dirname(abspath)
            for f in os.listdir(parent_dir):
                nf = os.path.join(parent_dir, f)
                if os.path.isdir(nf):
                    nd = os.path.join(testdir, f)
                    shutil.copytree(nf.decode("utf-8"), nd.decode("utf-8"))
                else:
                    shutil.copy(nf.decode("utf-8"), testdir.decode("utf-8"))
            #
            try:
                os.chdir(testdir)
                return my_testfile(abspath, shell, indent=indent,
                                cleanenv=cleanenv, debug=debug,
                                testname=path)
            finally:
                os.chdir(cwd)

        yield (path, test)

######################## _cli.py

from cram._encoding import b, bytestype, stdoutb
from cram._process import execute

__all__ = ['runcli']

def _prompt(question, answers, auto=None):
    """Write a prompt to stdout and ask for answer in stdin.

    answers should be a string, with each character a single
    answer. An uppercase letter is considered the default answer.

    If an invalid answer is given, this asks again until it gets a
    valid one.

    If auto is set, the question is answered automatically with the
    specified value.
    """
    default = [c for c in answers if c.isupper()]
    while True:
        sys.stdout.write('%s [%s] ' % (question, answers))
        sys.stdout.flush()
        if auto is not None:
            sys.stdout.write(auto + '\n')
            sys.stdout.flush()
            return auto

        answer = sys.stdin.readline().strip().lower()
        if not answer and default:
            return default[0]
        elif answer and answer in answers.lower():
            return answer

def _log(msg=None, verbosemsg=None, verbose=False):
    """Write msg to standard out and flush.

    If verbose is True, write verbosemsg instead.
    """
    if verbose:
        msg = verbosemsg
    if msg:
        if isinstance(msg, bytestype):
            stdoutb.write(msg)
        else: # pragma: nocover
            sys.stdout.write(msg)
        sys.stdout.flush()

def _patch(cmd, diff):
    """Run echo [lines from diff] | cmd -p0"""
    out, retcode = execute([cmd, '-p0'], stdin=b('').join(diff))
    return retcode == 0

def my_runcli(tests, quiet=False, verbose=False, patchcmd=None, answer=None):
    """Run tests with command line interface input/output.

    tests should be a sequence of 2-tuples containing the following:

        (test path, test function)

    This function yields a new sequence where each test function is wrapped
    with a function that handles CLI input/output.

    If quiet is True, diffs aren't printed. If verbose is True,
    filenames and status information are printed.

    If patchcmd is set, a prompt is written to stdout asking if
    changed output should be merged back into the original test. The
    answer is read from stdin. If 'y', the test is patched using patch
    based on the changed output.
    """
    total, skipped, failed = [0], [0], [0]

    for path, test in tests:
        def testwrapper():
            """Test function that adds CLI output"""
            total[0] += 1
            # _log(None, path + b(': '), verbose)
            # _log(b('File "') + path + b('": \n'), path + b(': '), verbose)

            refout, postout, diff = test()
            if refout is None:
                skipped[0] += 1
                _log('s', 'empty\n', verbose)
                return refout, postout, diff

            abspath = os.path.abspath(path)
            errpath = abspath + b('.err')

            if postout is None:
                skipped[0] += 1
                # _log('', 'skipped\n', verbose) #_log('s', 'skipped\n', verbose)
            elif not diff:
                # _log('', 'passed\n', verbose) #_log('.', 'passed\n', verbose)
                if os.path.exists(errpath):
                    os.remove(errpath)
            else:
                failed[0] += 1
                _log(b('File "') + path + b('": \n'), path + b(': '), verbose)
                # _log('', 'failed\n', verbose) #_log('!', 'failed\n', verbose)
                # if not quiet:
                #     _log('\n', None, verbose)

                errfile = open(errpath, 'wb')
                try:
                    for line in postout:
                        errfile.write(line)
                finally:
                    errfile.close()

                if not quiet:
                    origdiff = diff
                    diff = []
                    for line in origdiff:
                        stdoutb.write(line)
                        diff.append(line)

                    if (patchcmd and
                        _prompt('Accept this change?', 'yN', answer) == 'y'):
                        if _patch(patchcmd, diff):
                            _log(None, path + b(': merged output\n'), verbose)
                            os.remove(errpath)
                        else:
                            _log(path + b(': merge failed\n'))

            return refout, postout, diff

        yield (path, testwrapper)

    # if total[0] > 0:
    #     _log('\n', None, verbose)
    #     _log('# Ran %s tests, %s skipped, %s failed.\n'
    #          % (total[0], skipped[0], failed[0]))

######################## _main.py

def my_main(args):
    """Main entry point.

    If you're thinking of using Cram in other Python code (e.g., unit tests),
    consider using the test() or testfile() functions instead.

    :param args: Script arguments (excluding script name)
    :type args: str
    :return: Exit code (non-zero on failure)
    :rtype: int
    """
    opts, paths, getusage = _parseopts(args)
    if opts.version:
        sys.stdout.write("""Cram CLI testing framework (version 0.7)

Copyright (C) 2010-2016 Brodie Rao <brodie@bitheap.org> and others
This is free software; see the source for copying conditions. There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
""")
        return

    conflicts = [('--yes', opts.yes, '--no', opts.no),
                 ('--quiet', opts.quiet, '--interactive', opts.interactive),
                 ('--debug', opts.debug, '--quiet', opts.quiet),
                 ('--debug', opts.debug, '--interactive', opts.interactive),
                 ('--debug', opts.debug, '--verbose', opts.verbose),
                 ('--debug', opts.debug, '--xunit-file', opts.xunit_file)]
    for s1, o1, s2, o2 in conflicts:
        if o1 and o2:
            sys.stderr.write('options %s and %s are mutually exclusive\n'
                             % (s1, s2))
            return 2

    shellcmd = _which(opts.shell)
    if not shellcmd:
        stderrb.write(b('shell not found: ') + fsencode(opts.shell) + b('\n'))
        return 2
    shell = [shellcmd]
    if opts.shell_opts:
        shell += shlex.split(opts.shell_opts)

    patchcmd = None
    if opts.interactive:
        patchcmd = _which('patch')
        if not patchcmd:
            sys.stderr.write('patch(1) required for -i\n')
            return 2

    if not paths:
        sys.stdout.write(getusage())
        return 2

    badpaths = [path for path in paths if not os.path.exists(path)]
    if badpaths:
        stderrb.write(b('no such file: ') + badpaths[0] + b('\n'))
        return 2

    if opts.yes:
        answer = 'y'
    elif opts.no:
        answer = 'n'
    else:
        answer = None

    tmpdir = os.environ['CRAMTMP'] = tempfile.mkdtemp('', 'cramtests-')
    tmpdirb = fsencode(tmpdir)
    proctmp = os.path.join(tmpdir, 'tmp')
    for s in ('TMPDIR', 'TEMP', 'TMP'):
        os.environ[s] = proctmp

    os.mkdir(proctmp)
    try:
        tests = my_runtests(paths, tmpdirb, shell, indent=opts.indent,
                         cleanenv=not opts.preserve_env, debug=opts.debug)
        if not opts.debug:
            tests = my_runcli(tests, quiet=opts.quiet, verbose=opts.verbose,
                           patchcmd=patchcmd, answer=answer)
            if opts.xunit_file is not None:
                tests = runxunit(tests, opts.xunit_file)

        hastests = False
        failed = False
        for path, test in tests:
            hastests = True
            refout, postout, diff = test()
            if diff:
                failed = True

        if not hastests:
            sys.stderr.write('no tests found\n')
            return 2

        return int(failed)
    finally:
        if opts.keep_tmpdir:
            stdoutb.write(b('# Kept temporary directory: ') + tmpdirb +
                          b('\n'))
        else:
            shutil.rmtree(tmpdir)

my_main(sys.argv[1:])