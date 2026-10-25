import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
