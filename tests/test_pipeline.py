import csv
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path
from src.generate_data import ROOT
from src.pipeline import clean_rows, percentile_nearest_rank, run_pipeline


class LogicTests(unittest.TestCase):
    def test_exact_duplicates_are_removed(self):
        clean,bad,n=clean_rows([{"id":"a","n":1}]*2,["id"],lambda r:r)
        self.assertEqual((len(clean),len(bad),n),(1,0,1))

    def test_conflicting_duplicate_stops_load(self):
        with self.assertRaisesRegex(ValueError,"Conflicting duplicate"):
            clean_rows([{"id":"a","n":1},{"id":"a","n":2}],["id"],lambda r:r)

    def test_bad_row_is_quarantined(self):
        def validate(r):
            if r["n"]<0: raise ValueError("negative")
            return r
        clean,bad,n=clean_rows([{"id":"a","n":-1}],["id"],validate)
        self.assertEqual(bad[0]["reason"],"negative")
        self.assertEqual(len(clean),0)

    def test_percentile_boundaries(self):
        self.assertEqual(percentile_nearest_rank(range(1,101)),95)
        self.assertEqual(percentile_nearest_rank([7]),7)
        self.assertIsNone(percentile_nearest_rank([]))


class WarehouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT/"data/warehouse/smartswitch.sqlite").exists(): run_pipeline()
        cls.db=sqlite3.connect(ROOT/"data/warehouse/smartswitch.sqlite")
        cls.s=json.loads((ROOT/"reports/summary.json").read_text())
        cls.q=json.loads((ROOT/"reports/data_quality.json").read_text())

    @classmethod
    def tearDownClass(cls): cls.db.close()

    def test_raw_reconciliations(self):
        for label in ["commands","telemetry"]:
            self.assertEqual(self.q[f"raw_{label}"],self.q[f"accepted_{label}"]+
                             self.q[f"duplicate_{label}"]+self.q[f"rejected_{label}"])

    def test_complete_grid_and_no_orphans(self):
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM fact_device_hour").fetchone()[0],
                         self.s["devices"]*self.s["days"]*24)
        self.assertEqual(self.db.execute("PRAGMA foreign_key_check").fetchall(),[])

    def test_join_does_not_inflate_counts(self):
        totals=self.db.execute("SELECT SUM(commands),SUM(successes),SUM(estimated_kwh) FROM v_daily_kpis").fetchone()
        self.assertEqual(totals[:2],(self.s["commands"],self.s["successes"]))
        self.assertAlmostEqual(totals[2],self.s["estimated_kwh"],places=5)

    def test_weighted_rates_match_fact(self):
        n,ok=self.db.execute("SELECT COUNT(*),SUM(status='SUCCESS') FROM fact_command").fetchone()
        self.assertAlmostEqual(ok/n,self.s["command_success_rate"])

    def test_sql_percentile_matches_python(self):
        result=self.db.execute("""WITH ranked AS (SELECT latency_ms, ROW_NUMBER() OVER(ORDER BY latency_ms) rn,
            COUNT(*) OVER() n FROM fact_command WHERE status='SUCCESS')
            SELECT MIN(latency_ms) FROM ranked WHERE rn>=CAST((95*n+99)/100 AS INTEGER)""").fetchone()[0]
        self.assertEqual(result,self.s["p95_latency_ms"])

    def test_energy_assumption_reconciles(self):
        self.assertAlmostEqual(self.s["assumed_baseline_kwh"]-self.s["estimated_kwh"],self.s["modeled_avoided_kwh"])

    def test_null_latency_does_not_become_zero(self):
        invalid=self.db.execute("SELECT COUNT(*) FROM fact_command WHERE status<>'SUCCESS' AND latency_ms IS NOT NULL").fetchone()[0]
        self.assertEqual(invalid,0)

    def test_demo_contains_explainable_incident(self):
        values=self.db.execute("SELECT firmware_version,1.0*SUM(status='SUCCESS')/COUNT(*) FROM fact_command GROUP BY firmware_version").fetchall()
        rates=dict(values)
        self.assertLess(rates["1.1.0"],rates["1.0.2"])
        self.assertLess(rates["1.1.0"],rates["1.1.1"])


if __name__=="__main__": unittest.main()
