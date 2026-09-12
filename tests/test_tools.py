import html
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'), str(ROOT/'scripts')]

class DemoTests(unittest.TestCase):
    def test_eight_cases_validate_with_sources(self):
        from run_demo import load_cases
        cases=load_cases(ROOT)
        self.assertEqual(len(cases),8)
    def test_demo_has_labels_and_eight_sections(self):
        from run_demo import load_cases, build_html
        text=build_html(load_cases(ROOT))
        self.assertIn('合成参考示例',text)
        self.assertIn('不调用模型',text)
        self.assertEqual(text.count('class="case"'),8)
    def test_demo_escapes_untrusted_text(self):
        from run_demo import load_cases, build_html
        cases=load_cases(ROOT)
        cases[0]['package']['task_understanding']='<script>alert(1)</script>'
        text=build_html(cases)
        self.assertNotIn('<script>alert(1)</script>',text)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;',text)
    def test_write_demo_creates_index_and_reports(self):
        from run_demo import write_demo
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'demo';write_demo(ROOT,out)
            self.assertTrue((out/'index.html').is_file())
            self.assertEqual(len(list(out.glob('*.md'))),8)
    def test_demo_does_not_overwrite_existing_directory(self):
        from run_demo import write_demo
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileExistsError):write_demo(ROOT,Path(td))
    def test_analysis_math(self):
        from run_demo import calculate_demo_metrics
        result=calculate_demo_metrics(ROOT)
        self.assertEqual(result['lead_growth_percent'],'44.0')
        self.assertEqual(result['order_growth_percent'],'8.0')
        self.assertEqual(result['new_lead_conversion_percent'],'7.5')
        self.assertEqual(result['conversion_change_percentage_points'],'-2.5')

class InstallTests(unittest.TestCase):
    def test_dry_run_does_not_create(self):
        from install import install_skill
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'skills'/'heihua-skill'
            install_skill(ROOT,dest,apply=False)
            self.assertFalse(dest.exists())
    def test_install_runtime_only(self):
        from install import install_skill
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'skills'/'heihua-skill'
            install_skill(ROOT,dest,apply=True)
            self.assertTrue((dest/'SKILL.md').exists())
            self.assertTrue((dest/'references'/'phrases.json').exists())
            self.assertTrue((dest/'scripts'/'heihua.py').exists())
            self.assertFalse((dest/'tests').exists())
            self.assertFalse((dest/'examples').exists())
    def test_install_refuses_overwrite(self):
        from install import install_skill
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'heihua-skill';dest.mkdir()
            (dest/'keep.txt').write_text('keep')
            with self.assertRaises(FileExistsError):install_skill(ROOT,dest,apply=True)
            self.assertEqual((dest/'keep.txt').read_text(),'keep')
    def test_install_requires_correct_folder_name(self):
        from install import install_skill
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):install_skill(ROOT,Path(td)/'wrong-name',apply=True)
    def test_install_requires_skill_entrypoint(self):
        from install import install_skill
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):install_skill(Path(td),Path(td)/'out'/'heihua-skill',apply=True)
    def test_installed_helper_can_load_its_assets(self):
        from install import install_skill
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'heihua-skill';install_skill(ROOT,dest,apply=True)
            run=subprocess.run([sys.executable,str(dest/'scripts'/'heihua.py'),'lookup','再完善一下'],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('候选',run.stdout)

if __name__=='__main__':unittest.main()
