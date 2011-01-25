# $Id$

'''
tests/test_script.py
--------------------
Who tests the testers?

Some short integration tests for our 'FSPythonScript' unit testing
utility class.
'''

__author__ = 'Richard Mitchell <richard.mitchell@isotoma.com>'
__docformat__ = 'restructuredtext en'
__version__ = '$Revision$'[11:-2]

import os
import tempfile
import unittest

import mock

from isotoma.zope.testpythonscript.script import FSPythonScript


class TestPythonScript_Integration(unittest.TestCase):

    output_script = """## Script to output stuff given to it
##bind container=container
##bind context=context
##bind namespace=namespace
##bind script=script
##bind state=state
##bind traverse_subpath=traverse_subpath
##parameters=pfoo=None,pbar=[],pbaz={}
##title=
##
return {
        'container': container,
        'context': context,
        'namespace': namespace,
        'script': script,
        'traverse_subpath': traverse_subpath,
        'state': state,
        'locals': locals(),
        'globals': globals()
}"""

    bind_test_script = \
"""## Script to output stuff given to it with different bindings
##bind container1=container
##bind context1=context
##bind namespace1=namespace
##bind script1=script
##bind state1=state
##bind traverse_subpath1=traverse_subpath
##parameters=
##title=
##
return {
        'container': container1,
        'context': context1,
        'namespace': namespace1,
        'script': script1,
        'traverse_subpath': traverse_subpath1,
        'state': state1,
        'locals': locals(),
        'globals': globals()
}"""

    bound_variables = ('container', 'context', 'namespace', 'script',
                       'traverse_subpath', 'state')

    def setUp(self):
        f, filename = tempfile.mkstemp(suffix='.py')
        f = os.fdopen(f, 'w')
        f.write(TestPythonScript_Integration.output_script)
        f.close()
        self.output_script_filename = filename

        f, filename = tempfile.mkstemp(suffix='.py')
        f = os.fdopen(f, 'w')
        f.write(TestPythonScript_Integration.bind_test_script)
        f.close()
        self.bind_test_script_filename = filename

    def tearDown(self):
        os.remove(self.output_script_filename)
        os.remove(self.bind_test_script_filename)

    def test_unbound_variables(self):
        p = FSPythonScript(self.output_script_filename)
        result = p()
        for var in TestPythonScript_Integration.bound_variables:
            self.assertEqual(result[var], None,
                             "Unbound variable %s is not None." % var)

    def test_bound_variables(self):
        variables = dict([(v, v) for v in 
                          TestPythonScript_Integration.bound_variables])
        p = FSPythonScript(self.output_script_filename, **variables)
        result = p()
        for var in TestPythonScript_Integration.bound_variables:
            self.assertEqual(result[var], var,
                             "Bound variable %s not set correctly." % var)

    def test_bound_variables_global(self):
        variables = dict([(v, v) for v in 
                          TestPythonScript_Integration.bound_variables])
        p = FSPythonScript(self.output_script_filename, **variables)
        result = p()
        for var in TestPythonScript_Integration.bound_variables:
            self.assertTrue(var in result['globals'],
                            "Bound variable is not global: %s" % var)

    def test_bound_variables_bind(self):
        variables = dict([(v, v) for v in 
                          TestPythonScript_Integration.bound_variables])
        p = FSPythonScript(self.bind_test_script_filename, **variables)
        result = p()
        for val in TestPythonScript_Integration.bound_variables:
            var = val+'1'
            self.assertEqual(result[val], val,
                             "Bound variable %s not set correctly." % var)
            self.assertEqual(result['globals'][var], val,
                             "Bound variable %s not set correctly." % var)

    def test_additional_globals_used(self):
        p = FSPythonScript(self.output_script_filename,
                           g={'foo':'bar', 'baz':'zog'})
        result = p()
        self.assertTrue('foo' in result['globals'],
                        "Additional globals not available in function.")
        self.assertEquals(result['globals']['foo'], 'bar',
                          "Additional globals not set correctly.")
        self.assertTrue('baz' in result['globals'],
                        "Additional globals not available in function.")
        self.assertEquals(result['globals']['baz'], 'zog',
                          "Additional globals not set correctly.")

    def test_additional_globals_override_bound_variables(self):
        p = FSPythonScript(self.output_script_filename, context='foo',
                           g={'context':'bar'})
        result = p()
        self.assertTrue('context' in result['globals'],
                        "Context not available in function.")
        self.assertEquals(result['context'], 'bar',
                          "Context not set correctly.")

    def test_default_parameters(self):
        p = FSPythonScript(self.output_script_filename)
        result = p()
        self.assertTrue('pfoo' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pfoo'], None,
                          "Parameter not set correctly.")
        self.assertTrue('pbar' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pbar'], [],
                          "Parameter not set correctly.")
        self.assertTrue('pbaz' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pbaz'], {},
                          "Parameter not set correctly.")

    def test_set_parameters(self):
        p = FSPythonScript(self.output_script_filename)
        result = p(pfoo='foo', pbar='bar')
        self.assertTrue('pfoo' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pfoo'], 'foo',
                          "Parameter not set correctly.")
        self.assertTrue('pbar' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pbar'], 'bar',
                          "Parameter not set correctly.")
        self.assertTrue('pbaz' in result['locals'],
                        "Parameter does not exist.")
        self.assertEquals(result['locals']['pbaz'], {},
                          "Parameter not set correctly.")

def test_suite():
    return unittest.makeSuite(TestPythonScript_Integration)

if __name__=='__main__':
    unittest.main()