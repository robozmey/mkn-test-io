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

from cram._cli import runcli
from cram._encoding import b, fsencode, stderrb, stdoutb
from cram._run import _walk, _findtests
# from cram._xunit import runxunits

from cram._main import _which, _expandpath, _OptionParser, _parseopts
from cram._run import * 

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
                shutil.copy(nf.decode("utf-8"), testdir.decode("utf-8"))
            #
            try:
                os.chdir(testdir)
                return testfile(abspath, shell, indent=indent,
                                cleanenv=cleanenv, debug=debug,
                                testname=path)
            finally:
                os.chdir(cwd)

        yield (path, test)


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
            tests = runcli(tests, quiet=opts.quiet, verbose=opts.verbose,
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

print(my_main(sys.argv[1:]))