#!/usr/bin/env python3
"""Test linting and structural integrity of SKILL.md."""

import re
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"


class TestSkillMdStructure(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SKILL_MD.exists(), "SKILL.md must exist")
        self.content = SKILL_MD.read_text(encoding="utf-8")

    def test_frontmatter(self):
        match = re.match(r"^---\n(.*?)\n---\n", self.content, re.DOTALL)
        self.assertIsNotNone(match, "Frontmatter block (--- ... ---) must be present")
        fm = match.group(1)
        self.assertIn("name: repo-reverse-engineer", fm)
        self.assertIn("description:", fm)

    def test_required_headings(self):
        required_headings = [
            "## When to Use",
            "## When NOT to Use",
            "## Inputs",
            "## Safety Rules",
            "## Modes",
            "## Output Folder Convention",
            "## No-Hallucination Rules",
            "## Citation Format Specification",
            "## Script Index",
            "## Invocation Examples",
            "## References",
            "## Audience Flag Behavior",
            "## Failure & Fallback Strategies",
            "## Parallelization Guidance",
        ]
        for heading in required_headings:
            self.assertIn(heading, self.content, f"Heading '{heading}' missing from SKILL.md")

    def test_phase_count(self):
        phases = re.findall(r"^## Phase (\d+):", self.content, re.MULTILINE)
        self.assertEqual(len(phases), 8, f"Expected 8 phases (0-7), found {len(phases)}: {phases}")
        self.assertEqual(sorted([int(p) for p in phases]), list(range(8)))

    def test_no_remaining_todos(self):
        self.assertNotIn("TODO", self.content, "SKILL.md still contains unfulfilled TODO placeholders")

    def test_references_and_modes(self):
        references = [
            "analysis-playbook.md",
            "output-templates.md",
            "large-repo-strategy.md",
            "mermaid-cheatsheet.md",
        ]
        for ref in references:
            self.assertIn(ref, self.content, f"Reference '{ref}' missing from SKILL.md")

        for mode in ["quick", "standard", "deep"]:
            self.assertIn(mode, self.content, f"Mode '{mode}' missing from SKILL.md")


if __name__ == "__main__":
    unittest.main()
