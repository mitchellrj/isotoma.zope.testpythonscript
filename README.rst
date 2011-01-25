isotoma.zope.testpythonscript
=============================

Provides simple classes to be used for unit testing PythonScript and
FSPythonScripts from Zope / Plone.

Uses the bare minimum of setup code and does not require Zope or
Plone to run.

Example usage
~~~~~~~~~~~~~
::
    
    >>> from isotoma.zope.testpythonscript import PythonScript
    >>> my_script = """## Script to output stuff given to it
    ... ##bind container=container
    ... ##bind context=context
    ... ##bind namespace=namespace
    ... ##bind script=script
    ... ##bind state=state
    ... ##bind traverse_subpath=traverse_subpath
    ... ##parameters=name=None
    ... ##title=
    ... ##
    ... return 'Hello world! Hello %s!' % name
    ... """
    >>> py_script = PythonScript(my_script, 'my_script')
    >>> py_script(name='Foo')
    'Hello world! Hello Foo'
    >>>

See the documentation of isotoma.zope.testpythonscript.script for full
details of the class and of FSPythonScript.

See isotoma.zope.testpythonscript.tests.test_script for more examples.