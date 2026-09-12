#!/usr/bin/env python3
"""验证并重放合成参考示例。不调用模型，不是端到端效果评测。"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from work_package import load_json, validate_package, render_markdown


def load_cases(root: Path) -> list[dict]:
    examples = root / 'examples'
    result = []
    for entry in load_json(examples / 'manifest.json'):
        input_path = (examples / entry['input']).resolve()
        output_path = (examples / entry['reference_output']).resolve()
        if not input_path.is_relative_to(examples.resolve()) or not output_path.is_relative_to(examples.resolve()):
            raise ValueError('案例路径必须位于 examples 内')
        package = load_json(output_path)
        errors = validate_package(package, output_path.parent)
        if errors:
            raise ValueError(entry['id'] + '\n' + '\n'.join(errors))
        result.append({**entry, 'package': package, 'input_text': input_path.read_text(encoding='utf-8')})
    return result


def calculate_demo_metrics(root: Path) -> dict[str, str]:
    path = root / 'examples' / '03-deeper-analysis' / 'metrics.csv'
    with path.open(encoding='utf-8-sig', newline='') as file:
        rows = list(csv.DictReader(file))
    if len(rows) != 2:
        raise ValueError('该算术演示仅接受两个月的模拟记录')
    old_leads, new_leads = (Decimal(row['leads']) for row in rows)
    old_orders, new_orders = (Decimal(row['orders']) for row in rows)
    if min(old_leads, new_leads, old_orders) <= 0:
        raise ValueError('示例分母必须大于零')
    def fmt(x: Decimal) -> str:
        return str(x.quantize(Decimal('0.1')))
    old_rate = old_orders / old_leads * 100
    new_rate = new_orders / new_leads * 100
    return {
        'lead_growth_percent': fmt((new_leads / old_leads - 1) * 100),
        'order_growth_percent': fmt((new_orders / old_orders - 1) * 100),
        'old_lead_conversion_percent': fmt(old_rate),
        'new_lead_conversion_percent': fmt(new_rate),
        'conversion_change_percentage_points': fmt(new_rate - old_rate),
        'note': '仅核对模拟 CSV 的算术，不验证行为推断或因果解释。'
    }


CSS = '''
:root{--ink:#172c2b;--muted:#64736f;--paper:#f4f6f2;--card:#fff;--line:#dce4dd;--accent:#22614e;--warm:#f4ead9}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.75 system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif}
aside{position:fixed;inset:0 auto 0 0;width:252px;padding:34px 22px;background:var(--ink);color:#ecf5ed;overflow:auto}
.brand{font-size:23px;font-weight:750;letter-spacing:-.5px}.subbrand{font-size:12px;color:#b2c9be;margin:5px 0 28px}nav a{display:block;text-decoration:none;color:#d4e3da;padding:12px 10px;border-radius:7px;margin:3px 0;font-size:13px}nav a:hover,nav a:focus{background:#29413b;color:white}.navnum{font-size:11px;opacity:.7;display:block;letter-spacing:2px}.sidefoot{font-size:12px;border-top:1px solid #456056;margin-top:25px;padding-top:20px;color:#b2c9be}
main{margin-left:252px;padding:48px 48px 80px;max-width:1510px}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--accent);font-weight:750}h1{font-size:42px;line-height:1.3;letter-spacing:-1.5px;margin:12px 0 16px}header p{max-width:790px;color:var(--muted);margin:0 0 20px}.chips{display:flex;gap:9px;flex-wrap:wrap;margin:20px 0 24px}.chip{background:#e4ece4;padding:5px 11px;border-radius:5px;font-size:12px}.notice{border-left:3px solid var(--accent);padding:13px 17px;background:#eaf0e8;font-size:13px;max-width:1040px}
.case{scroll-margin-top:24px;margin-top:46px;border-top:1px solid var(--line);padding-top:30px}.casetop{display:flex;align-items:baseline;gap:17px}.case-number{color:var(--accent);font-size:15px;letter-spacing:2px;font-weight:750}h2{font-size:26px;line-height:1.4;margin:0 0 10px}.highlight{color:var(--muted);font-size:14px;margin:0 0 19px}.grid{display:grid;grid-template-columns:minmax(280px,.85fr) minmax(360px,1.15fr);gap:20px}.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:26px}.panel-input{background:#eaf0e8}.label{font-size:12px;letter-spacing:1px;font-weight:750;color:var(--accent);margin-bottom:14px}.quote{font-size:23px;line-height:1.65;font-weight:600;margin:0 0 24px}.context-label{font-size:13px;font-weight:700}.context{padding-left:20px;margin:8px 0;color:#4a6058;font-size:13px}.context li{margin:8px 0}.understanding{font-size:17px;line-height:1.85;margin:0 0 18px}.status{display:inline-block;border:1px solid #bbd4c4;background:#f4f8f2;border-radius:5px;padding:4px 10px;font-size:12px;margin-bottom:15px}.metricrow{display:flex;gap:8px;flex-wrap:wrap;font-size:12px}.metric{padding:3px 9px;background:#edf1ed;border-radius:4px}.smalltitle{font-size:13px;font-weight:750;margin:19px 0 6px}.compact{padding-left:19px;margin:8px 0;font-size:14px}.compact li{margin:7px 0}.reply{background:var(--ink);color:#f3f8f3;padding:22px 26px;border-radius:10px;margin-top:18px}.reply .label{color:#bbd8c8;margin-bottom:8px}.reply p{margin:0;font-size:15px;line-height:1.95}.stop{padding:14px 0 0;font-size:13px;color:#53655e}details{margin-top:17px;background:#fff;border:1px solid var(--line);border-radius:8px}summary{cursor:pointer;padding:13px 18px;color:var(--accent);font-size:13px;font-weight:650}pre{white-space:pre-wrap;word-break:break-word;padding:0 20px 20px;line-height:1.8;font-size:13px;font-family:inherit;margin:0}footer{margin-top:50px;padding-top:22px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}a:focus-visible,summary:focus-visible{outline:3px solid #99bbaa;outline-offset:3px}
@media(max-width:1050px){aside{width:210px;padding:25px 16px}main{margin-left:210px;padding:32px 25px}.grid{grid-template-columns:1fr}h1{font-size:34px}}
@media(max-width:680px){aside{position:static;width:auto;padding:20px}nav{display:flex;overflow:auto;gap:5px}nav a{min-width:170px}.sidefoot,.subbrand{display:none}main{margin:0;padding:28px 18px}h1{font-size:30px}.panel{padding:20px}.quote{font-size:21px}.casetop{gap:10px}h2{font-size:22px}}
@media print{aside{display:none}main{margin:0;padding:0}.case{break-before:page}.grid{grid-template-columns:1fr 1fr}.reply{background:white;color:black;border:1px solid #aaa}details{display:none}}
'''


def build_html(cases: list[dict]) -> str:
    nav = ''.join(f'<a href="#{escape(c["id"])}"><span class="navnum">{i:02d} / 08</span>{escape(c["title"])}</a>' for i,c in enumerate(cases,1))
    sections = []
    for i,c in enumerate(cases,1):
        d = c['package']; questions = len(d['clarifications'])
        ready = sum(t['state']=='ready' for t in d['tasks'])
        gates = sum(not g['confirmed'] for g in d['approval_gates'])
        context = ''.join('<li>'+escape(x['text'])+'</li>' for x in d['facts'][1:]) or '<li>没有说明对象，也没有提供材料。</li>'
        delivery = ''.join('<li>'+escape(x['name'])+'，'+escape(x['format'])+'。'+('建议，未确认。' if x['status']=='proposed' else '有明确依据。')+'</li>' for x in d['deliverables'])
        qs = ''.join('<li>'+escape(x['question'])+'</li>' for x in d['clarifications']) or '<li>本轮不追加问题，不代表审批门槛已经解除。</li>'
        boundary = ''.join('<li>'+escape(x)+'</li>' for x in d['out_of_scope'][:3])
        state = {'ready':'可先开工','partial':'部分可开工，部分等待','blocked':'先确认对象或前提'}[d['execution_status']]
        sections.append(f'''<section class="case" id="{escape(c['id'])}">
<div class="casetop"><span class="case-number">{i:02d}</span><h2>{escape(c['title'])}</h2></div>
<p class="highlight">{escape(c['highlight'])}</p>
<div class="grid"><div class="panel panel-input"><div class="label">输入 · 上级原话</div>
<p class="quote">{escape(d['request'])}</p><div class="context-label">已经知道的事</div><ul class="context">{context}</ul></div>
<div class="panel"><div class="label">输出 · 可以交接的工作包</div><span class="status">{state}</span>
<p class="understanding">{escape(d['task_understanding'])}</p>
<div class="metricrow"><span class="metric">必要问题 {questions} 个</span><span class="metric">无外部阻塞任务 {ready} 项</span><span class="metric">待授权门槛 {gates} 项</span></div>
<div class="smalltitle">先交什么</div><ul class="compact">{delivery}</ul>
<div class="smalltitle">需要确认什么</div><ul class="compact">{qs}</ul>
<div class="smalltitle">这次不做什么</div><ul class="compact">{boundary}</ul></div></div>
<div class="reply"><div class="label">可以复制的回复草稿 · 不会自动发送</div><p>{escape(d['reply_draft'])}</p></div>
<div class="stop"><strong>做到这里就停。</strong>{escape(d['stop_condition'])}</div>
<details><summary>查看完整工作包，包括假设、任务依赖与依据</summary><pre>{escape(render_markdown(d))}</pre></details>
<details><summary>查看完整模拟输入</summary><pre>{escape(c['input_text'])}</pre></details>
</section>''')
    return '<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>heihua-skill · 办公任务解码演示</title><style>'+CSS+'</style></head><body>' + f'''<aside><div class="brand">heihua-skill</div><div class="subbrand">把模糊要求变成可开工的任务</div><nav aria-label="案例导航">{nav}</nav><div class="sidefoot">第10类 · 超级个体进化营<br>v0.1.0 · 2026年9月12日<br>纯本地展示，无外部资源。</div></aside><main>
<header><div class="eyebrow">办公任务解码 · 可复用工作流</div><h1>先弄清要交什么，<br>再开始干。</h1><p>不把再完善一下翻译成无限加内容。先查已有信息，再确定最小交付、必要问题和不能越过的边界。</p>
<div class="chips"><span class="chip">60条候选情景规则</span><span class="chip">8个办公案例</span><span class="chip">事实与假设分开</span><span class="chip">只问影响行动的问题</span></div>
<div class="notice">这是合成参考示例，数据与场景均为模拟。此页面重放仓库中的参考工作包，不调用模型，不代表真实用户效果或竞品对测结果。</div></header>
{''.join(sections)}<footer>实际使用时由宿主模型读取 SKILL.md 和真实授权材料后生成工作包。校验通过不等于意图判断正确，工作包也不是执行授权。</footer></main></body></html>'''


def write_demo(root: Path, output: Path) -> None:
    cases = load_cases(root)
    metrics = calculate_demo_metrics(root)
    if output.exists():
        raise FileExistsError('演示输出目录已存在，请指定新的目录，避免覆盖用户文件。')
    output.mkdir(parents=True)
    for case in cases:
        (output / (case['id']+'.md')).write_text(render_markdown(case['package']),encoding='utf-8')
    (output/'index.html').write_text(build_html(cases),encoding='utf-8')
    (output/'metrics-check.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'validation.json').write_text(json.dumps({'cases_checked':len(cases),'literal_source_quotes_checked':True,
        'status':'passed','live_model_run':False,'note':'只验证参考示例的结构、引用和约束。'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'output'/'demo')
    parser.add_argument('--check',action='store_true',help='只检查，不写文件')
    args=parser.parse_args()
    try:
        if args.check:
            cases=load_cases(ROOT)
            print(f'PASS，{len(cases)} 个合成参考示例，未调用模型。')
            print(json.dumps(calculate_demo_metrics(ROOT),ensure_ascii=False,indent=2))
        else:
            write_demo(ROOT,args.output)
            print('已生成 '+str(args.output/'index.html')+'，重放参考输出，未调用模型。')
        return 0
    except (OSError,ValueError,UnicodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 1

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
