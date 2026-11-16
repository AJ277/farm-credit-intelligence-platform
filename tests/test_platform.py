import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/platform.sh"
USDA = ROOT / "components/usda-data-engineering"

class PlatformIntegrationTests(unittest.TestCase):
    def launch(self, *args):
        result = subprocess.run([str(LAUNCHER), *args], cwd=ROOT, capture_output=True, text=True, check=True, timeout=120)
        return json.loads(result.stdout)

    def test_01_component_repositories(self):
        for name in ("autonomous-agent", "document-intelligence", "financial-risk", "usda-data-engineering"):
            self.assertTrue((ROOT / "components" / name / "README.md").is_file(), name)

    def test_02_financial_and_document_preflight(self):
        result = self.launch("preflight")
        self.assertEqual(result["financial"]["status"], "ready")
        self.assertEqual(result["documents"]["status"], "ready")

    def test_03_financial_retrieval(self):
        rows = self.launch("finance", "--limit", "5")
        self.assertEqual(len(rows), 5)
        self.assertTrue(all("institution_name" in row for row in rows))

    def test_04_document_retrieval(self):
        rows = self.launch("documents", "Farm Credit System funding conditions", "--mode", "lexical")
        self.assertGreater(len(rows), 0)
        self.assertTrue(all("url" in row and "page" in row for row in rows))

    def test_05_usda_preflight(self):
        source = USDA / "data/raw/usda_corn_all_states_original.csv"
        self.assertTrue(source.is_file(), "USDA source CSV missing")
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-m", "src.preflight", "--csv", str(source), "--clean-out", str(Path(directory) / "clean.csv"), "--report", str(Path(directory) / "audit.json")], cwd=USDA, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stderr)
            audit = json.loads((Path(directory) / "audit.json").read_text())
            self.assertEqual(audit["counts"]["eligible_numeric_rows"], 252)

if __name__ == "__main__":
    unittest.main()
