import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class CliTests(unittest.TestCase):
    def run_cli(self, actual, example, *options):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual_path = root / 'actual.env'
            example_path = root / 'sample.env.example'
            actual_path.write_bytes(actual if isinstance(actual, bytes) else actual.encode('utf-8'))
            example_path.write_bytes(example if isinstance(example, bytes) else example.encode('utf-8'))
            return subprocess.run(
                [sys.executable, '-m', 'env_contract', str(actual_path), '--example', str(example_path), *options],
                capture_output=True, text=True, encoding='utf-8', check=False,
            )

    def test_cli_success_never_displays_values(self):
        result = self.run_cli('API_KEY=SYNTHETIC_SECRET\n', 'API_KEY=\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('SYNTHETIC_SECRET', result.stdout + result.stderr)

    def test_cli_missing_key(self):
        result = self.run_cli('PORT=8000\n', 'PORT=\nAPI_KEY=\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('API_KEY', result.stdout)

    def test_io_error_is_safe(self):
        result = subprocess.run([sys.executable, '-m', 'env_contract', 'definitely-missing.env'],
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_help(self):
        result = subprocess.run([sys.executable, '-m', 'env_contract', '--help'],
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--example', result.stdout)

    def test_secret_not_printed_on_invalid_quote(self):
        secret = 'SYNTHETIC_SECRET_MUST_NOT_APPEAR'
        result = self.run_cli('API_KEY="' + secret + '\n', 'API_KEY=\n')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(secret, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_invalid_encoding_is_safe(self):
        result = self.run_cli(b'KEY=\xff', 'KEY=\n')
        self.assertEqual(result.returncode, 2)
        self.assertIn('invalid_encoding', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_bom_file_and_empty_value(self):
        result = self.run_cli('\ufeffKEY=" "\r\n', 'KEY=\r\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Empty: KEY', result.stdout)

    def test_json_schema_and_exit_codes(self):
        expected_fields = {'schema_version', 'missing', 'empty', 'unexpected', 'duplicates', 'invalid_lines', 'errors', 'ok'}
        cases = [
            ('KEY=demo\n', 'KEY=\n', [], 0),
            ('KEY=demo\nEXTRA=demo\n', 'KEY=\n', [], 0),
            ('KEY=demo\nEXTRA=demo\n', 'KEY=\n', ['--strict'], 1),
            ('KEY=\n', 'KEY=\n', [], 1),
            ('KEY=a\nKEY=b\n', 'KEY=\n', [], 1),
            ('KEY="SYNTHETIC_SECRET\n', 'KEY=\n', ['--strict'], 2),
            (b'KEY=\xff', 'KEY=\n', [], 2),
        ]
        for actual, example, options, code in cases:
            with self.subTest(code=code, options=options, actual=repr(actual)):
                result = self.run_cli(actual, example, '--json', *options)
                self.assertEqual(result.returncode, code, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(set(report), expected_fields)
                self.assertEqual(report['schema_version'], 1)
                self.assertEqual(report['ok'], code == 0)
                self.assertNotIn('SYNTHETIC_SECRET', result.stdout + result.stderr)
                self.assertEqual(result.stderr, '')

    def test_json_file_error(self):
        result = subprocess.run([sys.executable, '-m', 'env_contract', 'missing.env', '--json'],
                                capture_output=True, text=True, encoding='utf-8', check=False)
        self.assertEqual(result.returncode, 2)
        self.assertTrue(json.loads(result.stdout)['errors'])

    def test_json_example_syntax_error(self):
        result = self.run_cli('KEY=demo\n', 'KEY="unclosed\n', '--json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['invalid_lines']['example'], [1])

    def test_string_io_streams_and_safe_exceptions(self):
        from env_contract.cli import main
        output = io.StringIO()
        with patch('sys.stdout', output), patch('sys.stderr', io.StringIO()), \
                patch('pathlib.Path.read_text', side_effect=OSError('SYNTHETIC_SECRET_ERROR')):
            code = main(['missing.env', '--json'])
        self.assertEqual(code, 2)
        self.assertNotIn('SYNTHETIC_SECRET_ERROR', output.getvalue())
        self.assertEqual(json.loads(output.getvalue())['errors'][0]['kind'], 'unreadable')

    def test_default_example_path(self):
        import os
        from env_contract.cli import main
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'actual.env').write_text('KEY=demo\n', encoding='utf-8')
            (root / '.env.example').write_text('KEY=\n', encoding='utf-8')
            try:
                os.chdir(root)
                with patch('sys.stdout', io.StringIO()):
                    self.assertEqual(main(['actual.env']), 0)
            finally:
                os.chdir(previous)
