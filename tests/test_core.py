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


class SyntaxTests(unittest.TestCase):
    def test_value_syntax_and_emptiness(self):
        cases = [
            ('KEY=', True, True), ('KEY=   ', True, True),
            ('KEY="   "', True, True), ("KEY='\t '", True, True),
            ('export KEY=demo', True, False), ("KEY='demo # value'", True, False),
            ('KEY=demo # comment', True, False), ('KEY= # comment', True, True),
            ('KEY=#literal', True, False), ('KEY=demo#literal', True, False),
            ('KEY="demo" # comment', True, False), ('KEY="demo" garbage', False, None),
            ('KEY="unclosed', False, None), ("KEY='unclosed", False, None),
            ('KEY="escaped\\\"quote"', True, False),
            ('KEY="escaped\\\"', False, None),
            ("KEY='backslash\\' trailing", False, None),
            ('KEY="${NOT_EXPANDED}"', True, False),
            ('KEY=$(not-executed)', True, False),
            ('BAD-KEY=demo', False, None), ('9KEY=demo', False, None),
        ]
        for line, valid, empty in cases:
            with self.subTest(line=line):
                document = parse_document(line)
                self.assertEqual(not document.invalid_lines, valid)
                if valid:
                    self.assertEqual(document.entries['KEY'][0].empty, empty)

    def test_bom_and_crlf(self):
        document = parse_document('\ufeffKEY=demo\r\nPORT=8000\r\n')
        self.assertEqual(document.invalid_lines, ())
        self.assertEqual(sorted(document.entries), ['KEY', 'PORT'])

    def test_expected_empty_values_are_still_required(self):
        result = compare_documents(parse_document(''), parse_document('KEY=\n'))
        self.assertEqual(result.missing, ['KEY'])

    def test_empty_expected_keys_fail_but_empty_extras_only_warn(self):
        result = compare_documents(parse_document('KEY=\nEXTRA=\n'), parse_document('KEY=\n'))
        self.assertEqual(result.empty, ['KEY'])
        self.assertEqual(result.unexpected, ['EXTRA'])
        self.assertEqual(result.exit_code(), 1)

    def test_duplicate_roles_and_all_line_numbers(self):
        result = compare_documents(parse_document('KEY=a\n\nKEY=b\n'), parse_document('KEY=\nKEY=\n'))
        self.assertEqual(result.duplicates, {'actual': {'KEY': [1, 3]}, 'example': {'KEY': [1, 2]}})
        self.assertEqual(result.exit_code(), 1)

    def test_multiline_quoted_values_are_invalid(self):
        document = parse_document('KEY="first\nsecond"\n')
        self.assertEqual(document.invalid_lines, (1, 2))

    def test_invalid_values_are_absent_from_representations(self):
        secret = 'SYNTHETIC_MALFORMED_SECRET'
        document = parse_document('KEY="' + secret)
        self.assertNotIn(secret, repr(document))

    def test_unclosed_multiline_value_cannot_become_a_reported_key(self):
        secret = 'SYNTHETIC_MULTILINE_SECRET'
        document = parse_document('KEY="first line\n' + secret + '=tail\n')
        self.assertNotIn(secret, repr(document))
        result = compare_documents(document, parse_document('KEY=\n'))
        self.assertNotIn(secret, repr(result))
        self.assertEqual(result.exit_code(), 2)
