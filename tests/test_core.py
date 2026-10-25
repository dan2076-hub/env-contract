import unittest

from env_contract.core import compare_documents, parse_document


class ContractTests(unittest.TestCase):
    def test_equal_keys(self):
        result = compare_documents(parse_document('PORT=9000\n'), parse_document('PORT=8000\n'))
        self.assertEqual(result.exit_code(), 0)

    def test_missing_and_unexpected_are_sorted(self):
        result = compare_documents(parse_document('Z=secret\nA=secret\n'), parse_document('D=\nB=\n'))
        self.assertEqual(result.missing, ['B', 'D'])
        self.assertEqual(result.unexpected, ['A', 'Z'])
        self.assertEqual(result.exit_code(), 1)

    def test_unexpected_is_a_warning(self):
        result = compare_documents(parse_document('EXTRA=secret\n'), parse_document(''))
        self.assertEqual(result.exit_code(), 0)

    def test_blank_lines_comments_and_export(self):
        document = parse_document('\n # comment\nexport API_KEY=demo\n PORT = 8000\n')
        self.assertEqual(sorted(document.entries), ['API_KEY', 'PORT'])
        self.assertEqual(document.invalid_lines, ())

    def test_result_objects_do_not_store_values(self):
        secret = 'SYNTHETIC_VALUE_MUST_NOT_APPEAR'
        document = parse_document('API_KEY=' + secret + '\n')
        result = compare_documents(document, parse_document('API_KEY=\n'))
        self.assertNotIn(secret, repr(document) + repr(result))

    def test_malformed_assignment_reports_only_line_number(self):
        document = parse_document('VALID=demo\nNOT AN ASSIGNMENT\n')
        self.assertEqual(document.invalid_lines, (2,))
        self.assertEqual(compare_documents(document, parse_document('')).exit_code(), 2)
