import unittest
from snowflake_backend import parse_route

class RouterTests(unittest.TestCase):
    def test_existing_customer_is_preserved(self):
        self.assertEqual(parse_route('{"intent":"evidence","customer":"Northstar Mobility"}', ['Northstar Mobility'])['customer'], 'Northstar Mobility')
    def test_unknown_customer_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_route('{"intent":"exposure","customer":"Unknown"}', ['Northstar Mobility'])
    def test_sql_in_place_of_intent_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_route('{"intent":"DROP TABLE CP_ORDERS","customer":null}', [])
    def test_extra_sql_field_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_route('{"intent":"exposure","customer":null,"sql":"select secret"}', [])
    def test_unsupported_is_explicit(self):
        self.assertEqual(parse_route('{"intent":"unsupported","customer":null}', [])['intent'], 'unsupported')
    def test_malformed_model_response_fails(self):
        with self.assertRaises(ValueError):
            parse_route('not json', [])
    def test_markdown_fenced_json_is_accepted(self):
        fenced = '```json\n{"intent":"exposure","customer":null}\n```'
        self.assertEqual(parse_route(fenced, [])['intent'], 'exposure')
    def test_snowpark_json_encoded_fenced_response(self):
        # AI_COMPLETE in Snowpark returns a JSON-encoded string wrapping fenced JSON
        encoded = '"```json\\n{\\n  \\"intent\\": \\"exposure\\",\\n  \\"customer\\": null\\n}\\n```"'
        result = parse_route(encoded, [])
        self.assertEqual(result['intent'], 'exposure')
        self.assertIsNone(result['customer'])
    def test_snowpark_json_encoded_plain_response(self):
        encoded = '"{\\"intent\\":\\"evidence\\",\\"customer\\":\\"Northstar Mobility\\"}"'
        self.assertEqual(parse_route(encoded, ['Northstar Mobility'])['customer'], 'Northstar Mobility')
    def test_snowpark_double_encoded_extra_field_rejected(self):
        encoded = '"{\\"intent\\":\\"exposure\\",\\"customer\\":null,\\"sql\\":\\"drop table\\"}"'
        with self.assertRaises(ValueError):
            parse_route(encoded, [])
