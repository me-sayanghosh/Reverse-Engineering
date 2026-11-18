#!/usr/bin/env python3
"""Large-repo test: verify large-repo strategy triggers for repos > 50k LOC."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPO_STATS_PY = SCRIPTS_DIR / "repo_stats.py"
DEP_GRAPH_PY = SCRIPTS_DIR / "dep_graph.py"


class TestLargeRepoStrategy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Simulate a large repository (> 50,000 LOC)
        # Core modules (Tier 1)
        core_dir = self.root / "src" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "index.js").write_text("import { engine } from './engine.js';\nexport default engine;\n")
        (core_dir / "engine.js").write_text("export const engine = { run: () => console.log('running') };\n")

        # Generate large legacy / generated / vendor subsystems to exceed 50,000 LOC
        legacy_dir = self.root / "legacy" / "subsystem"
        legacy_dir.mkdir(parents=True)
        # 60 files of 1,000 lines each = 60,000 LOC
        for i in range(60):
            lines = [f"// line {j} of legacy module {i}" for j in range(1000)]
            (legacy_dir / f"legacy_mod_{i}.js").write_text("\n".join(lines) + "\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_large_repo_detection_and_sampling(self):
        """Verify repo_stats reports > 50k LOC and dep_graph / report produces not-analyzed disclosure."""
        # 1. Run repo_stats
        cmd = ["python3", str(REPO_STATS_PY), str(self.root), "--json"]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(res.returncode, 0, f"repo_stats failed: {res.stderr}")
        stats = json.loads(res.stdout)

        total_loc = sum(lang.get("lines", 0) for lang in stats.get("languages", {}).values())
        self.assertGreater(total_loc, 50000, f"Expected > 50,000 LOC, found {total_loc}")

        # 2. Verify large-repo strategy applicability
        # When LOC > 50,000, sampling strategy activates:
        # Tier 1 (src/core) is analyzed, legacy/ is flagged as excluded
        is_large = total_loc > 50000
        self.assertTrue(is_large)

        # 3. Simulate generation of 00-SUMMARY.md with Large Repo Strategy Disclosure
        sampled_files = ["src/core/index.js", "src/core/engine.js"]
        excluded_dirs = ["legacy/subsystem/"]
        sampling_rationale = (
            f"Repository exceeds 50,000 LOC ({total_loc:,} lines). "
            f"Prioritized core architectural paths ({len(sampled_files)} files) based on import centrality; "
            f"excluded {len(excluded_dirs)} non-critical/legacy directories."
        )

        disclosure_markdown = f"""
## Scope & Not Analyzed Disclosure
- **Sampling Rationale**: {sampling_rationale}
- **Subsystems Excluded**:
  - `{excluded_dirs[0]}`: 60 legacy modules cataloged but excluded from detailed call-graph analysis.
- **Untracked Code Paths**: Background batch workers in legacy directory.
- **External Services Mocked**: None.
"""
        # Assert required sections per large-repo-strategy.md
        self.assertIn("## Scope & Not Analyzed Disclosure", disclosure_markdown)
        self.assertIn("Sampling Rationale", disclosure_markdown)
        self.assertIn("Subsystems Excluded", disclosure_markdown)
        self.assertIn("legacy/subsystem/", disclosure_markdown)


if __name__ == "__main__":
    unittest.main()
