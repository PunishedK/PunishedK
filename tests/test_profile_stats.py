import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from ensure_stats_section import START, END, update_readme
from update_profile_stats import render_svg, write_if_changed


class ProfileStatsTests(unittest.TestCase):
    def test_svg_themes_are_valid_and_show_values(self):
        for theme in ("light", "dark"):
            svg = render_svg((102, 85, 11, 7), theme)
            ET.fromstring(svg)
            for value in ("102", "85", "11", "7"):
                self.assertIn(f">{value}<", svg)
            self.assertIn("CONTRIBUTIONS / 12M", svg)

    def test_svg_output_is_deterministic(self):
        values = (102, 85, 11, 7)
        self.assertEqual(render_svg(values, "dark"), render_svg(values, "dark"))

    def test_write_only_if_changed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assets" / "stats.svg"
            self.assertTrue(write_if_changed(path, "first"))
            self.assertFalse(write_if_changed(path, "first"))
            self.assertTrue(write_if_changed(path, "second"))

    def test_readme_preserved_and_idempotent(self):
        original = "# Banner\n\n![snake](assets/snake.svg)\n\n### Contributions\n\nContent\n"
        once = update_readme(original)
        self.assertEqual(update_readme(once), once)
        self.assertIn("![snake]", once)
        self.assertEqual(once.count(START), 1)
        self.assertEqual(once.count(END), 1)
        self.assertLess(once.index(START), once.index("### Contributions"))

    def test_readme_without_contribution_heading(self):
        once = update_readme("# Profile\n")
        self.assertEqual(once, update_readme(once))


if __name__ == "__main__":
    unittest.main()
