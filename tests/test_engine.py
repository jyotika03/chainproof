import copy
import json
from pathlib import Path
import unittest
from engine import evaluate

DATA = json.loads((Path(__file__).resolve().parents[1] / 'data/demo.json').read_text())


class ExposureTests(unittest.TestCase):
    def test_multiple_late_shipments_do_not_double_count_order_value(self):
        result = evaluate(DATA)
        self.assertEqual(result['exposed_value_inr'], 2000000)
        self.assertEqual(result['exposed_orders'], ['O-201', 'O-202'])
        self.assertEqual(len(result['evidence']), 3)

    def test_recovery_keeps_orders_with_other_late_inputs_exposed(self):
        result = evaluate(DATA, {'S-101': '2026-10-06'})
        self.assertEqual(result['exposed_orders'], ['O-201'])
        self.assertEqual(result['exposed_value_inr'], 1200000)

    def test_arrival_on_needed_date_is_on_time(self):
        result = evaluate(DATA, {'S-101': '2026-10-06', 'S-102': '2026-10-06'})
        self.assertEqual(result['exposed_value_inr'], 0)

    def test_missing_allocation_target_is_rejected(self):
        data = copy.deepcopy(DATA)
        data['allocations'][0]['order_id'] = 'missing'
        with self.assertRaises(ValueError):
            evaluate(data)

    def test_unknown_scenario_target_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(DATA, {'missing': '2026-10-01'})

    def test_scenario_does_not_change_source(self):
        original = copy.deepcopy(DATA)
        evaluate(DATA, {'S-101': '2026-10-06'})
        self.assertEqual(DATA, original)


if __name__ == '__main__':
    unittest.main()
