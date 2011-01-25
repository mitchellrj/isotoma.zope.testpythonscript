# $Id$

'''
tests/script.py
---------------
'''

__author__ = 'Richard Mitchell <richard.mitchell@isotoma.com>'
__docformat__ = 'restructuredtext en'
__version__ = '$Revision$'[11:-2]

import os
import re
from StringIO import StringIO

from indent_finder import IndentFinder
import mock


class PythonScript:
    """ This class is designed to run .py, .cpy & .vpy files from Zope /
        Plone with the bare minimum of code for unit testing purposes.
        Beware that using this script runner will not flag up errors in
        incorrect use of restricted python. This also means that use of
        this could result in nasty things happening, though if your unit
        tests have nasty side-effects, that's your own fault.

        Everything you may normally expect should be mocked
        (acquisition, state, context, etc.)

        Initialisation returns a callable object, which may be called
        with keyword parameters as if it were called from the web with
        those parameters.
    """

    def __init__(self, text, id, container=None, context=None, namespace=None,
                 script=None, traverse_subpath=None, state=None, g={}):
        """ Wraps an existing Plone-style python script and makes it
            runnable.

            text     is a file-like object, or the full text of the
                     script to wrap.

            id=None  is the id given to the function. By default will be
                     set to the basename of the file, less the extension
                     and any invalid characters.

            container, context, namespace, script, traverse_subpath,
            state
                     may all be substituted with values which they
                     should take when the script is run.

            g={}     a dictionary of variables which should be global
                     when the script is run.
        """

        if isinstance(text, basestring):
            self._scriptbuffer = StringIO(text)
        else:
            self._scriptbuffer = text
        self._fileheader = []
        self._signature = {}
        self._filecontents = []
        self._compiled_code = None
        self._id = id
        self.container = container
        self.context = context
        self.namespace = namespace
        self.script = script
        self.traverse_subpath = traverse_subpath
        self.state = state
        self._parameters = {}
        self._use_kwargs = ''
        self._tab = ' '*4

        self._setglobals = g
        self._globals = {}

    def _parseHeaders(self):
        """ Parses the binds and parameters set in the comments in the
            header of Zope/Plone scripts and stores them in the object
            for later.
        """

        self._globals = dict([(k, '__me__._getGlobal("%s")'%k)
                              for k in self._setglobals])
        for line in self._fileheader:
            line = line[2:].strip()
            # binds
            if line.startswith('bind'):
                match = re.match(r'^bind\s+([^\s=]+)\s*=\s*([^\s]+)$', line)
                if match:
                    key, value = match.groups()
                    value = 'getattr(__me__, "%(v)s", "%(v)s")' % {'v': value}
                    self._globals.setdefault(key, value)
            # parameters
            if line.startswith('parameters'):
                match = re.match(r'^parameters\s*=\s*(.*?)\s*$', line)
                if match:
                    params = match.group(1)
                    kwargs = re.search(',?(\*\*[^,$]+)\w*(,|$)', params)
                    if kwargs:
                        self._use_kwargs = kwargs.group(1)
                        params = re.sub(',?\*\*[^,$]+\w*(,|$)', '\\1', params)
                    self._signature = eval('dict('+params+')')

    def _getGlobal(self, n):
        """ Used within the script wrapper function to retrieve globals
            set at initialization.
        """

        return self._setglobals[n]

    def _compileFunction(self):
        """ Wraps the script code in a function and then our own wrapper
            function and stores it in the object for execution later.
        """

        # set the function signature up based on the parameters from the header
        sig = ','.join(['%s=%r' % (k, v)
                        for k,v in self._signature.items()])
        if self._use_kwargs:
            sig = (sig and sig+', ' or '') + self._use_kwargs
        f = ['def ' + self._id + '('+sig+'):\n']

        # apply indent
        for line in self._filecontents:
            f.append(self._tab + line)

        # wrap in our own function which will set up 'globals'
        code = ['def compiled_code(__me__, **kwargs):',
                self._tab + self._tab.join(['global %s\n' % k
                                            for k in self._globals]),
                self._tab,
                self._tab + self._tab.join(['%s=%s\n' % (k,v)
                                            for k, v in \
                                            self._globals.items()]),
                self._tab,
                self._tab + self._tab.join(f),
                self._tab,
                self._tab + 'return '+self._id+'(**kwargs)\n']
        code = '\n'.join(code)

        exec code
        self._compiled_code = compiled_code

    def _runFunction(self, **kwargs):
        """ Passes the keyword arguments to the script, less any which
            do not appear in the parameters list at the head of the
            script; runs the script and returns the result.
        """

        dels = []
        params = kwargs.copy()
        # least efficient looping ever.
        # kill off any kwargs that we don't expect in the signature
        for k in params:
            if k not in self._signature:
                dels.append(k)
        for d in dels:
            del params[d]

        return self._compiled_code(self, **params)
    
    def reloadContent(self):
        """ Reloads the script contents from the file system.
        """

        self._fileheader = []
        self._filecontents = []
        self._scriptbuffer.seek(0)
        fi = IndentFinder()

        for line in self._scriptbuffer.readlines():
            fi.analyse_line(line)
            if line.startswith('##'):
                self._fileheader.append(line.strip())
            else:
                self._filecontents.append(line)

        indent_results = fi.results()
        if indent_results[0]=='mixed':
            raise ValueError("Code indented with mixed tabs/spaces.")
        else:
            self._tab = ' '*indent_results[1]

        self._parseHeaders()
        self._compileFunction()

    def __call__(self, **kwargs):
        """ (Re)loads the script from the filesystem and runs it,
            returning the result. Any keyword arguments passed to this
            function are passed on to the script.
        """

        self.reloadContent()
        return self._runFunction(**kwargs)


class FSPythonScript(PythonScript):

    def __init__(self, filename, id=None, container=None, context=None,
                 namespace=None, script=None, traverse_subpath=None,
                 state=None, g={}):
        """ Wraps an existing Plone-style python script and makes it
            runnable.

            filename is the full path to the file which we should wrap

            id=None  is the id given to the function. By default will be
                     set to the basename of the file, less the extension
                     and any invalid characters.

            container, context, namespace, script, traverse_subpath,
            state
                     may all be substituted with values which they
                     should take when the script is run.

            g={}     a dictionary of variables which should be global
                     when the script is run.
        """

        # Try to open the file before we proceed, that way we raise any
        # filesystem errors early.
        self._scriptbuffer = open(filename, 'r')
        self._scriptbuffer.close()

        self.__filename = filename
        self._id = id or \
                   re.sub(r'[^\w_]', '',
                          os.path.basename(filename).rsplit('.',1)[0])
        self._fileheader = []
        self._signature = {}
        self._filecontents = []
        self._compiled_code = None
        self.container = container
        self.context = context
        self.namespace = namespace
        self.script = script
        self.traverse_subpath = traverse_subpath
        self.state = state
        self._parameters = {}
        self._use_kwargs = ''
        self._tab = ' '*4

        self._setglobals = g
        self._globals = {}
        

    def reloadContent(self):
        """ Reloads the script contents from the file system.
        """

        self._scriptbuffer = open(self.__filename, 'r')
        PythonScript.reloadContent(self)
        self._scriptbuffer.close()