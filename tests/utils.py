#!/usr/bin/env python

"""
To test standard input (without piped data), run each of:

* csvclean
* csvcut -c 1
* csvformat
* csvgrep -c 1 -m d
* csvjson --no-inference --stream --snifflimit 0
* csvstack
* in2csv --format csv --no-inference --snifflimit 0

And paste:

"a","b","c"
"g","h","i"
"d","e","f"

"""

import sys
import unittest
import warnings
from contextlib import contextmanager
from io import StringIO

import agate

from csvkit.exceptions import ColumnIdentifierError, RequiredHeaderError


@contextmanager
def stderr_as_stdout():
    temp = sys.stderr
    sys.stderr = sys.stdout
    yield
    sys.stderr = temp


@contextmanager
def stdin_as_string(content):
    temp = sys.stdin
    sys.stdin = content
    yield
    sys.stdin = temp


class CSVKitTestCase(unittest.TestCase):
    warnings.filterwarnings(action='ignore', module='agate')

    def get_output(self, args):
        output_file = StringIO()

        utility = self.Utility(args, output_file)
        utility.run()

        output = output_file.getvalue()
        output_file.close()

        return output

    def get_output_as_io(self, args):
        return StringIO(self.get_output(args))

    def get_output_as_list(self, args):
        return self.get_output(args).split('\n')

    def get_output_as_reader(self, args):
        return agate.csv.reader(self.get_output_as_io(args))

    def assertRows(self, args, rows):
        reader = self.get_output_as_reader(args)

        for row in rows:
            self.assertEqual(next(reader), row)

        self.assertRaises(StopIteration, next, reader)

    def assertLines(self, args, rows, newline_at_eof=True):
        lines = self.get_output_as_list(args)

        if newline_at_eof:
            rows.append('')

        for i, row in enumerate(rows):
            self.assertEqual(lines[i], row)

        self.assertEqual(len(lines), len(rows))


class EmptyFileTests:
    def test_empty(self):
        with open('examples/empty.csv') as f, stdin_as_string(f):
            utility = self.Utility(getattr(self, 'default_args', []))
            utility.run()


class NamesTests:
    def test_names(self):
        output = self.get_output_as_io(['-n', 'examples/dummy.csv'])

        self.assertEqual(next(output), '  1: a\n')
        self.assertEqual(next(output), '  2: b\n')
        self.assertEqual(next(output), '  3: c\n')

    def test_invalid_options(self):
        args = ['-n', '--no-header-row', 'examples/dummy.csv']

        output_file = StringIO()
        utility = self.Utility(args, output_file)

        with self.assertRaises(RequiredHeaderError):
            utility.run()

        output_file.close()


class ColumnsTests:
    def test_invalid_column(self):
        args = getattr(self, 'columns_args', []) + ['-c', '0', 'examples/dummy.csv']

        output_file = StringIO()
        utility = self.Utility(args, output_file)

        with self.assertRaises(ColumnIdentifierError):
            utility.run()

        output_file.close()
