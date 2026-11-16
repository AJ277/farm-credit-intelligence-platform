import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "output/combined_report.md"

class CombinedReportTests(unittest.TestCase):
    def test_combined_report(self):
        result = subprocess.run(
            [str(ROOT / "scripts/platform.sh"), "combined-report"],
            cwd=ROOT, capture_output=True, text=True, timeout=120
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(REPORT.is_file())
        text = REPORT.read_text(encoding="utf-8")
        for section in (
            "FCA Financial Screening",
            "USDA Agricultural Indicators",
            "FCA Document References",
            "Interpretation and Limitations",
        ):
            self.assertIn(section, text)
        self.assertIn("2026Q3", text)
        self.assertIn("2025", text)
        self.assertIn("No institution-specific geographic", text)
        self.assertIn("https://www.fca.gov/", text)
        self.assertIn("https://quickstats.nass.usda.gov/", text)

if __name__ == "__main__":
    unittest.main()
