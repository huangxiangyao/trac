# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2020 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at https://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at https://trac.edgewall.org/log/.

from __future__ import absolute_import

import os
import re
import textwrap
import unittest
from pkg_resources import parse_version

from genshi.core import Stream, TEXT
from genshi.input import HTMLParser

try:
    import pygments
    have_pygments = True
except ImportError:
    have_pygments = False

import trac.tests.compat
from trac.mimeview.api import LineNumberAnnotator, Mimeview
if have_pygments:
    from trac.mimeview.pygments import PygmentsRenderer
from trac.test import EnvironmentStub, MockRequest
from trac.util import get_pkginfo
from trac.web.chrome import Chrome, web_context
from trac.wiki.formatter import format_to_html


if have_pygments:
    pygments_version = parse_version(get_pkginfo(pygments).get('version'))


class PygmentsRendererTestCase(unittest.TestCase):

    def setUp(self):
        self.env = EnvironmentStub(enable=[Chrome, LineNumberAnnotator,
                                           PygmentsRenderer])
        self.pygments = Mimeview(self.env).renderers[0]
        self.req = MockRequest(self.env)
        self.context = web_context(self.req)
        pygments_html = open(os.path.join(os.path.split(__file__)[0],
                                       'pygments.html'))
        self.pygments_html = Stream(list(HTMLParser(pygments_html, encoding='utf-8')))

    @property
    def python_mimetype(self):
        if pygments_version >= parse_version('2.5.0'):
            return 'text/x-python2'
        else:
            return 'text/x-python'

    def _expected(self, expected_id):
        return self.pygments_html.select(
            '//div[@id="%s"]/*|//div[@id="%s"]/text())' %
            (expected_id, expected_id))

    def _test(self, expected_id, result):
        expected = unicode(self._expected(expected_id))
        result = unicode(result)
        #print("\nE: " + repr(expected))
        #print("\nR: " + repr(result))
        self.assertEqual(re.split(r'(<[^>]*>)', expected),
                         re.split(r'(<[^>]*>)', result))

    def test_python_hello(self):
        """
        Simple Python highlighting with Pygments (direct)
        """
        result = self.pygments.render(self.context, self.python_mimetype,
                                      textwrap.dedent("""
            def hello():
                    return "Hello World!"
            """))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_hello', result)
        else:
            self._test('python_hello_pygments_2.1plus', result)

    def test_python_hello_mimeview(self):
        """
        Simple Python highlighting with Pygments (through Mimeview.render)
        """
        result = Mimeview(self.env).render(self.context, self.python_mimetype,
                                           textwrap.dedent("""
            def hello():
                    return "Hello World!"
            """))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_hello_mimeview', result)
        else:
            self._test('python_hello_mimeview_pygments_2.1plus', result)

    def test_python_with_lineno(self):
        result = format_to_html(self.env, self.context, textwrap.dedent("""\
            {{{#!%s lineno
            print 'this is a python sample'
            a = b+3
            z = "this is a string"
            print 'this is the end of the python sample'
            }}}
            """ % self.python_mimetype))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_with_lineno_1', result)
        else:
            self._test('python_with_lineno_1_pygments_2.1plus', result)

        result = format_to_html(self.env, self.context, textwrap.dedent("""\
            {{{#!%s lineno=3
            print 'this is a python sample'
            a = b+3
            z = "this is a string"
            print 'this is the end of the python sample'
            }}}
            """ % self.python_mimetype))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_with_lineno_2', result)
        else:
            self._test('python_with_lineno_2_pygments_2.1plus', result)

    def test_python_with_lineno_and_markups(self):
        """Python highlighting with Pygments and lineno annotator
        """
        result = format_to_html(self.env, self.context, textwrap.dedent("""\
            {{{#!%s lineno=3 id=b marks=4-5
            print 'this is a python sample'
            a = b+3
            z = "this is a string"
            print 'this is the end of the python sample'
            }}}
            """ % self.python_mimetype))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_with_lineno_and_markups', result)
        else:
            self._test('python_with_lineno_and_markups_pygments_2.1plus', result)

    def test_python_with_invalid_arguments(self):
        result = format_to_html(self.env, self.context, textwrap.dedent("""\
            {{{#!%s lineno=-10
            print 'this is a python sample'
            a = b+3
            z = "this is a string"
            print 'this is the end of the python sample'
            }}}
            """ % self.python_mimetype))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_with_invalid_arguments_1', result)
        else:
            self._test('python_with_invalid_arguments_1_pygments_2.1plus', result)

        result = format_to_html(self.env, self.context, textwrap.dedent("""\
            {{{#!%s lineno=a id=d marks=a-b
            print 'this is a python sample'
            a = b+3
            z = "this is a string"
            print 'this is the end of the python sample'
            }}}
            """ % self.python_mimetype))
        self.assertTrue(result)
        if pygments_version < parse_version('2.1'):
            self._test('python_with_invalid_arguments_2', result)
        else:
            self._test('python_with_invalid_arguments_2_pygments_2.1plus', result)

    def test_pygments_lexer_options(self):
        self.env.config.set('pygments-lexer',
                            'php.startinline', True)
        self.env.config.set('pygments-lexer',
                            'php.funcnamehighlighting', False)
        result = format_to_html(self.env, self.context, textwrap.dedent("""
            {{{#!php
            if (class_exists('MyClass')) {
                $myclass = new MyClass();
            }
            }}}
            """))
        self.assertTrue(result)
        self._test('pygments_lexer_options', result)

    def test_pygments_lexer_arguments(self):
        result = format_to_html(self.env, self.context, textwrap.dedent("""
            {{{#!php startinline=True funcnamehighlighting=False
            if (class_exists('MyClass')) {
                $myclass = new MyClass();
            }
            }}}
            """))
        self.assertTrue(result)
        self._test('pygments_lexer_arguments', result)

    def test_pygments_lexer_arguments_override_options(self):
        self.env.config.set('pygments-lexer',
                            'php.startinline', True)
        self.env.config.set('pygments-lexer',
                            'php.funcnamehighlighting', False)
        result = format_to_html(self.env, self.context, textwrap.dedent("""
            {{{#!php funcnamehighlighting=True
            if (class_exists('MyClass')) {
                $myclass = new MyClass();
            }
            }}}
            """))
        self.assertTrue(result)
        self._test('pygments_lexer_arguments_override_options', result)

    def test_newline_content(self):
        """
        The behavior of Pygments changed post-Pygments 0.11.1, and now
        contains all four newlines.  In Pygments 0.11.1 and prior, it only
        has three since stripnl defaults to True.

        See https://trac.edgewall.org/ticket/7705.
        """
        from pkg_resources import parse_version, get_distribution

        result = self.pygments.render(self.context, self.python_mimetype,
                                      '\n\n\n\n')
        self.assertTrue(result)
        t = "".join([r[1] for r in result if r[0] is TEXT])

        if parse_version(pygments.__version__) > parse_version('0.11.1') \
           or pygments.__version__ == '0.11.1' and 'dev' in \
           get_distribution('Pygments').version:
            self.assertEqual("\n\n\n\n", t)
        else:
            self.assertEqual("\n\n\n", t)

    def test_empty_content(self):
        """
        A '\n' token is generated for an empty file, so we have to bypass
        pygments when rendering empty files.
        """
        result = self.pygments.render(self.context, self.python_mimetype, '')
        self.assertIsNone(result)

    def test_extra_mimetypes(self):
        """
        The text/x-ini mimetype is normally not known by Trac, but
        Pygments supports it.
        """
        mimeview = Mimeview(self.env)
        self.assertIn(mimeview.get_mimetype('file.ini'),
                      ('text/x-ini; charset=utf-8',
                       'text/inf; charset=utf-8'))  # Pygment 2.1+
        self.assertIn(mimeview.get_mimetype('file.cfg'),
                      ('text/x-ini; charset=utf-8',
                       'text/inf; charset=utf-8'))  # Pygment 2.1+
        self.assertEqual('text/x-ini; charset=utf-8',
                         mimeview.get_mimetype('file.text/x-ini'))

def test_suite():
    suite = unittest.TestSuite()
    if have_pygments:
        suite.addTest(unittest.makeSuite(PygmentsRendererTestCase))
    else:
        print('SKIP: mimeview/tests/pygments (no pygments installed)')
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
