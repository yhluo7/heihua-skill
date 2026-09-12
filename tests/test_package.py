"""行为测试。每项拒绝条件都有实际 CLI 输入，而非模拟工具返回。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import contextlib
import io
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts' / 'heihua.py'
sys.path.insert(0, str(ROOT / 'scripts'))

def invoke(args):
    from heihua import main
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(args)
    return SimpleNamespace(returncode=code, stdout=out.getvalue(), stderr=err.getvalue())

def sample():
    return {
        'schema_version': '1.0', 'request': '先拉一个框架。',
        'task_understanding': '先拟内部讨论提纲，不生成完整方案。',
        'execution_status': 'ready',
        'evidence': [{'id':'E1','source':'input.request','quote':'先拉一个框架。'}],
        'facts': [{'text':'先交框架。','evidence_ids':['E1']}],
        'interpretations': [{'meaning':'先形成供讨论的提纲。','confidence':'medium','evidence_ids':['E1'],'selected':True,'would_change':'若要求完整方案，需要再确认范围。'}],
        'assumptions': [{'id':'A1','text':'暂按内部讨论使用。','risk':'low','reversible':True,'check_at':'提纲反馈时。','fallback':'调整受众和结构。'}],
        'question_policy': {'budget':2,'exception_reason':''},
        'clarifications': [],
        'deliverables': [{'id':'D1','name':'讨论提纲','format':'Markdown','status':'proposed','evidence_ids':[],'acceptance':['列明讨论目标和待决定问题。']}],
        'tasks': [{'id':'T1','action':'整理讨论目标和提纲。','deliverable_id':'D1','depends_on':[],'state':'ready','acceptance':['提纲可供确认。'],'timebox':'建议先用20分钟。'}],
        'approval_gates': [],
        'risks':[{'risk':'受众尚未明确。','impact':'可能需调整表达。','mitigation':'只做可修改的内部提纲。','evidence_ids':[]}],
        'out_of_scope':['不承诺预算和实施日期。'],
        'reply_draft':'我先列内部讨论提纲，暂不扩成完整方案。',
        'stop_condition':'提纲能支持一次范围确认即可停止。'
    }

class PackageTests(unittest.TestCase):
    def run_cli(self, data, command='check', extra=()):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'工作包.json'
            path.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            return invoke([command,str(path),*extra])
    def rejects(self,data,code):
        p=self.run_cli(data)
        self.assertEqual(p.returncode,1,p.stderr+p.stdout)
        self.assertIn(code,p.stderr+p.stdout)
    def test_valid_package(self):
        p=self.run_cli(sample()); self.assertEqual(p.returncode,0,p.stderr+p.stdout)
    def test_render_contains_reply_and_stop(self):
        p=self.run_cli(sample(),'render'); self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('给上级的回复草稿',p.stdout);self.assertIn('做到这里就停',p.stdout)
    def test_required_field(self):
        d=sample();del d['stop_condition'];self.rejects(d,'SCHEMA')
    def test_reject_unknown_field(self):
        d=sample();d['secret']='x';self.rejects(d,'SCHEMA')
    def test_reject_string_boolean(self):
        d=sample();d['interpretations'][0]['selected']='yes';self.rejects(d,'SCHEMA')
    def test_reject_missing_evidence(self):
        d=sample();d['facts'][0]['evidence_ids']=['E99'];self.rejects(d,'EVIDENCE_REF')
    def test_reject_fact_without_evidence(self):
        d=sample();d['facts'][0]['evidence_ids']=[];self.rejects(d,'SCHEMA')
    def test_reject_duplicate_evidence(self):
        d=sample();d['evidence'].append(copy.deepcopy(d['evidence'][0]));self.rejects(d,'DUPLICATE_ID')
    def test_reject_request_quote_not_present(self):
        d=sample();d['evidence'][0]['quote']='老板批准了100万元';self.rejects(d,'QUOTE_MISMATCH')
    def test_reject_no_selected_interpretation(self):
        d=sample();d['interpretations'][0]['selected']=False;self.rejects(d,'INTERPRETATION')
    def test_reject_two_selected_interpretations(self):
        d=sample();d['interpretations'].append(copy.deepcopy(d['interpretations'][0]));self.rejects(d,'INTERPRETATION')
    def test_reject_forward_dependency(self):
        d=sample();d['tasks'][0]['depends_on']=['T2'];self.rejects(d,'TASK_DEPENDENCY')
    def test_reject_self_dependency(self):
        d=sample();d['tasks'][0]['depends_on']=['T1'];self.rejects(d,'TASK_DEPENDENCY')
    def test_reject_missing_deliverable(self):
        d=sample();d['tasks'][0]['deliverable_id']='D2';self.rejects(d,'DELIVERABLE_REF')
    def test_reject_ungated_waiting_task(self):
        d=sample();d['tasks'][0]['state']='waiting';d['execution_status']='blocked';self.rejects(d,'UNEXPLAINED_WAIT')
    def test_reject_unapproved_gate_ready_task(self):
        d=sample();d['approval_gates']=[{'id':'G1','reason':'需审批。','confirmed':False,'evidence_ids':[],'blocks':['T1']}];self.rejects(d,'GATE_BYPASS')
    def test_valid_blocked_work(self):
        d=sample();d['tasks'][0]['state']='waiting';d['execution_status']='blocked'
        d['approval_gates']=[{'id':'G1','reason':'需审批。','confirmed':False,'evidence_ids':[],'blocks':['T1']}]
        p=self.run_cli(d);self.assertEqual(p.returncode,0,p.stderr)
    def test_reject_approval_without_evidence(self):
        d=sample();d['approval_gates']=[{'id':'G1','reason':'需审批。','confirmed':True,'evidence_ids':[],'blocks':['T1']}];self.rejects(d,'APPROVAL_EVIDENCE')
    def test_reject_inconsistent_status(self):
        d=sample();d['execution_status']='blocked';self.rejects(d,'STATUS')
    def test_reject_question_budget(self):
        d=sample();d['clarifications']=[{'id':f'Q{i}','question':'确认受众。','why_needed':'影响工作。','changes':'改变范围。','if_no_answer':'仅列提纲。','blocks':[]} for i in range(1,4)];self.rejects(d,'QUESTION_BUDGET')
    def test_reject_budget_without_reason(self):
        d=sample();d['question_policy']['budget']=3;self.rejects(d,'QUESTION_EXCEPTION')
    def test_reject_empty_acceptance(self):
        d=sample();d['tasks'][0]['acceptance']=[];self.rejects(d,'SCHEMA')
    def test_unicode_bom_input(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'中文.json';p.write_text(json.dumps(sample(),ensure_ascii=False),encoding='utf-8-sig')
            run=subprocess.run([sys.executable,str(CLI),'check',str(p)],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(run.returncode,0,run.stderr)
    def test_malformed_json_has_friendly_error(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json';p.write_text('{',encoding='utf-8')
            run=subprocess.run([sys.executable,str(CLI),'check',str(p)],capture_output=True,text=True,encoding='utf-8')
            self.assertNotEqual(run.returncode,0);self.assertIn('INPUT',run.stderr);self.assertNotIn('Traceback',run.stderr)
    def test_lookup_known_phrase(self):
        p=invoke(['lookup','再完善一下'])
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('候选',p.stdout)
    def test_lookup_unknown_does_not_invent(self):
        p=invoke(['lookup','xyznonexistent8721'])
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('未匹配',p.stdout)
    def test_reject_path_escape(self):
        with tempfile.TemporaryDirectory() as td:
            d=sample();d['evidence'][0]['source']='../secret.txt'
            self.rejects_with_root(d,td,'SOURCE_PATH')
    def rejects_with_root(self,d,root,code):
        p=self.run_cli(d,extra=('--source-root',str(root)))
        self.assertEqual(p.returncode,1,p.stderr);self.assertIn(code,p.stderr)
    def test_reject_missing_source_file(self):
        with tempfile.TemporaryDirectory() as td:
            d=sample();d['evidence'][0]['source']='missing.md';self.rejects_with_root(d,td,'SOURCE_MISSING')
    def test_source_quote_validation(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'context.md').write_text('先拉一个框架。',encoding='utf-8')
            d=sample();d['evidence'][0]['source']='context.md'
            p=self.run_cli(d,extra=('--source-root',str(td)))
            self.assertEqual(p.returncode,0,p.stderr)
    def test_reject_irreversible_assumption(self):
        d=sample();d['assumptions'][0]['reversible']=False;self.rejects(d,'IRREVERSIBLE_ASSUMPTION')
    def test_reject_downstream_ready_from_waiting(self):
        d=sample();d['tasks'][0]['state']='waiting';d['execution_status']='partial'
        d['approval_gates']=[{'id':'G1','reason':'需审批。','confirmed':False,'evidence_ids':[],'blocks':['T1']}]
        t=copy.deepcopy(d['tasks'][0]);t.update(id='T2',depends_on=['T1'],state='ready');d['tasks'].append(t)
        self.rejects(d,'DEPENDENCY_BYPASS')
    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json';p.write_text('{"x":1,"x":2}',encoding='utf-8')
            run=subprocess.run([sys.executable,str(CLI),'check',str(p)],capture_output=True,text=True,encoding='utf-8')
            self.assertNotEqual(run.returncode,0);self.assertIn('重复',run.stderr)

if __name__=='__main__':unittest.main()
