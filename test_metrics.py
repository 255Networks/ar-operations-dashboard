import json
import unittest
from pathlib import Path

from metrics import business_hours, metrics, moment


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name("data.json").read_text())
        self.m = metrics(self.data)

    def test_flow(self):
        self.assertEqual([self.m[k] for k in ("opening","new","reopened","closures","ending")], [1,4,1,3,3])

    def test_transfer_and_close_attribution(self):
        self.assertEqual(self.m["team"]["East"]["closures"],2)
        self.assertEqual(self.m["team"]["West"]["open"],2)

    def test_response_denominator(self):
        self.assertEqual(self.m["responses"],{"met":2,"missed":1,"pending":1})

    def test_automation(self):
        self.assertEqual(self.m["automation"],{"ai_confirm":2,"ai_override":1})

    def test_hold_time_and_cycle(self):
        self.assertEqual(self.m["waiting"],8)
        self.assertEqual(self.m["median_cycle"],6)

    def test_distinct_invoices(self):
        self.assertEqual(self.m["unique_exposure"],460)
        self.assertEqual(sum(r["usd"] for r in self.m["open_cases"]),860)

    def test_weekend(self):
        self.assertEqual(business_hours(moment("2026-04-03 16:00"),moment("2026-04-06 10:00")),2)

    def test_end_excluded(self):
        self.data["tickets"][-1]["events"].append([self.data["end"],"close",""])
        self.assertEqual(metrics(self.data)["ending"],3)

    def test_shared_invoice_conflict(self):
        self.data["tickets"][2]["usd"] += 1
        with self.assertRaises(ValueError):
            metrics(self.data)

    def test_invalid_reopen(self):
        self.data["tickets"][-1]["events"].append(["2026-04-10 16:15","reopen",""])
        with self.assertRaises(ValueError):
            metrics(self.data)
