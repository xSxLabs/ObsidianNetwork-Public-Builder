#!/usr/bin/env python3
"""Reject false 10/50/100 wireless stress PASS from incomplete or bad CI logs."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"features/wireless-energy/validate-wireless-density-report.py"
spec=importlib.util.spec_from_file_location("wireless_density_report",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def line(count,sink=None):
    return f"WIRELESS_DENSE_REAL_SERVER_{count}_V1 PASS total={count*256000} sink={sink or count*16000}"


class DensityReportTest(unittest.TestCase):
    def setUp(self):
        self.good="\n".join((line(10),line(50),line(100),
                              "WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS"))

    def test_real_valid_phases(self):
        parsed=module.verify(self.good)
        self.assertEqual([p["receivers"] for p in parsed["phases"]],[10,50,100])
        self.assertTrue(parsed["idle_after_100_pass"])
        self.assertIn("NOT Spark",parsed["scope"])

    def test_missing_duplicated_or_invalid_balances_rejected(self):
        for bad in (
            self.good.replace(line(50),""),
            self.good+"\n"+line(100),
            self.good.replace(line(10),line(10,1).replace("total=2560000","total=2559999")),
            self.good.replace("sink=160000","sink=0"),
            self.good.replace("WIRELESS_DENSE_IDLE_RECEIVERS_100_V1 PASS",""),
            self.good.replace(line(50),line(50,99_999_999)),
        ):
            with self.subTest(bad=bad[-90:]):
                with self.assertRaises(ValueError):
                    module.verify(bad)

    def test_ci_echo_is_not_evidence(self):
        malicious="\n".join(f'grep -Fq "{ln}" file.log' for ln in self.good.splitlines())
        with self.assertRaises(ValueError):
            module.verify(malicious)


if __name__=="__main__":
    unittest.main()
