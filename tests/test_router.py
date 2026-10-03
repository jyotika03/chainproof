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
