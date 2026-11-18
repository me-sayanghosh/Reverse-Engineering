import unittest
import re
from pathlib import Path

class TestSampleCitations(unittest.TestCase):
    def setUp(self):
        self.skill_root = Path(__file__).resolve().parent.parent
        self.sample_dir = self.skill_root / "examples" / "sample-output"
        self.demo_app = self.skill_root / "tests" / "fixtures" / "demo-app"
        self.citation_re = re.compile(r"([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+):(\d+)")

    def test_sample_citations_resolve(self):
        reports = ["00-SUMMARY.md", "01-ARCHITECTURE.md", "03-API-AND-DATA.md"]
        total_checked = 0
        for report in reports:
            file_path = self.sample_dir / report
            self.assertTrue(file_path.exists(), f"Sample report missing: {report}")
            text = file_path.read_text()
            matches = self.citation_re.findall(text)
            for path_str, line_str in matches:
                if path_str == "localhost" or path_str.endswith(".com") or path_str.endswith(".org"):
                    continue
                target_file = self.demo_app / path_str
                line_num = int(line_str)
                self.assertTrue(target_file.exists(), f"{report}: referenced file {path_str} does not exist")
                lines = target_file.read_text().splitlines()
                self.assertTrue(1 <= line_num <= len(lines), f"{report}: line {line_num} out of range for {path_str}")
                total_checked += 1
        self.assertGreaterEqual(total_checked, 15, f"Expected at least 15 citations, found {total_checked}")

if __name__ == "__main__":
    unittest.main()
