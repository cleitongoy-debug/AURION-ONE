"""Regression tests for original Evolution 5058 HTML navigation, no network or disk scans."""
import pathlib
import re
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "AURION_ONE.py"
def html():
    data = SOURCE.read_text(encoding="utf-8")
    return data.split('HTML = r"""', 1)[1].split('"""', 1)[0]

class EvolutionDomTest(unittest.TestCase):
    def test_ids_unique(self):
        ids = re.findall(r'\\bid="([^"]+)"', html())
        repeated = sorted({value for value in ids if ids.count(value) > 1})
        self.assertEqual(repeated, [], f"Duplicated DOM id: {repeated}")

    def test_both_library_sections_preserved(self):
        body = html()
        self.assertIn('id="library-traces"', body)
        self.assertIn('id="library"', body)
        self.assertIn('tab(\\'library-traces\\',this)', body)
        self.assertIn('tab(\\'library\\',this);libraryLoad()', body)

    def test_space_section_and_inner_list_distinct(self):
        body = html()
        self.assertIn('<section id="spaces" class="tab">',body)
        self.assertIn('<div id="spaces-items"></div>',body)
        self.assertIn("document.getElementById('spaces-items')",body)

    def test_catalog_is_not_rescanned_on_navigation(self):
        body=html()
        self.assertIn('tab(\\'library\\',this);libraryLoad()', body)
        self.assertIn('async function libraryScan()', body)
        self.assertIn('CATALOGAR DISCO LOCAL E EXTERNO',body)
        # Navigation should load cache, not call the disk scan endpoint.
        self.assertNotIn('tab(\\'library\\',this);libraryScan()', body)

    def test_existing_study_and_models_survive(self):
        body=html()
        for tag in ('id="sessions"','id="bridge"','id="studyClock"','id="trifaseStatus"'):
            self.assertIn(tag,body)

if __name__=="__main__":
    unittest.main()
