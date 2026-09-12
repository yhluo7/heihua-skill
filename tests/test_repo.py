from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))

class RepoCheckTests(unittest.TestCase):
    def test_frontmatter_accepts_current_skill(self):
        from check_repo import frontmatter_errors
        self.assertEqual(frontmatter_errors((ROOT/'SKILL.md').read_text(encoding='utf-8')),[])
    def test_frontmatter_rejects_bad_name(self):
        from check_repo import frontmatter_errors
        self.assertTrue(frontmatter_errors('---\nname: Wrong Name\ndescription: test\n---\n'))
    def test_frontmatter_requires_description(self):
        from check_repo import frontmatter_errors
        self.assertTrue(frontmatter_errors('---\nname: heihua-skill\n---\n'))
    def test_local_link_checks_missing_file(self):
        from check_repo import markdown_link_errors
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'README.md';p.write_text('[说明](missing.md)',encoding='utf-8')
            self.assertTrue(markdown_link_errors(p,root))
    def test_external_links_and_code_blocks_are_ignored(self):
        from check_repo import markdown_link_errors
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'README.md'
            p.write_text('[外部](https://example.com)\n```text\n[x](not-a-file.md)\n```\n',encoding='utf-8')
            self.assertEqual(markdown_link_errors(p,root),[])
    def test_reference_style_link_is_checked(self):
        from check_repo import markdown_link_errors
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'README.md';p.write_text('[说明][x]\n\n[x]: missing.md\n',encoding='utf-8')
            self.assertTrue(markdown_link_errors(p,root))
    def test_relative_link_outside_repo_is_rejected(self):
        from check_repo import markdown_link_errors
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'README.md';p.write_text('[越界](../secret.md)',encoding='utf-8')
            self.assertTrue(markdown_link_errors(p,root))

if __name__=='__main__':unittest.main()
