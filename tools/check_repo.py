#!/usr/bin/env python3
"""检查当前发布包的文件、引用和参考示例。只做本地静态检查，不测模型。"""
from __future__ import annotations
import ast
import hashlib
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from work_package import load_json, render_markdown, validate_package

REQUIRED=(
    'SKILL.md','README.md','LICENSE','agents/openai.yaml',
    'references/phrases.json','assets/work-package.schema.json',
    'examples/manifest.json','docs/research/competitors.md',
    'docs/research/sources.json','docs/demo/index.html','docs/demo/preview.png',
    'docs/testing/VERIFICATION.md','eval/README.md','eval/cases.json',
    'tools/install.py','tools/run_demo.py','.github/workflows/check.yml',
)

def frontmatter_errors(text: str) -> list[str]:
    """检查本项目使用的简单 frontmatter，不是通用 YAML 解析器。"""
    errors=[]
    if not text.startswith('---\n'):
        return ['SKILL.md 缺少 YAML frontmatter']
    end=text.find('\n---',4)
    if end<0:
        return ['SKILL.md frontmatter 没有闭合']
    head=text[4:end]
    name=re.search(r'^name:\s*(.*?)\s*$',head,re.M)
    desc=re.search(r'^description:\s*(.*?)\s*$',head,re.M)
    if not name or name.group(1)!='heihua-skill':
        errors.append('SKILL.md name 必须是 heihua-skill')
    if not desc or not 1<=len(desc.group(1))<=1024:
        errors.append('SKILL.md description 必须是1至1024字符的单行说明')
    if len(text.splitlines())>500:
        errors.append('SKILL.md 超过本项目500行限制')
    return errors


def markdown_link_errors(path: Path, root: Path) -> list[str]:
    """检查文档内相对文件链接。不验证网页和页内锚点，不实现完整 Markdown。"""
    text=path.read_text(encoding='utf-8')
    text=re.sub(r'```.*?```','',text,flags=re.S)
    targets=re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)',text)
    targets+=re.findall(r'^\[[^\]\n]+\]:\s*(\S+)',text,re.M)
    errors=[]
    for raw in targets:
        target=raw.strip().split(' ',1)[0].strip('<>')
        parts=urlsplit(target)
        if parts.scheme or parts.netloc or not parts.path:
            continue
        dest=(path.parent/unquote(parts.path)).resolve()
        label=f'{path.relative_to(root)} -> {target}'
        if not dest.is_relative_to(root.resolve()):
            errors.append('链接越出仓库，'+label)
        elif not dest.exists():
            errors.append('链接目标不存在，'+label)
    return errors


def check_repo(root: Path) -> list[str]:
    root=root.resolve(); errors=[]
    for rel in REQUIRED:
        if not (root/rel).is_file(): errors.append('缺少文件，'+rel)
    if (root/'SKILL.md').is_file():
        errors+=frontmatter_errors((root/'SKILL.md').read_text(encoding='utf-8'))
    for path in root.rglob('*'):
        if not path.is_file() or any(p in {'.git','__pycache__','output','dist','.venv'} for p in path.relative_to(root).parts):
            continue
        try:
            if path.suffix=='.json': load_json(path)
            elif path.suffix=='.py': ast.parse(path.read_text(encoding='utf-8'),filename=str(path),feature_version=(3,10))
            elif path.suffix=='.md': errors+=markdown_link_errors(path,root)
        except (OSError,ValueError,UnicodeError,SyntaxError) as exc:
            errors.append(f'{path.relative_to(root)}，{exc}')
    try:
        phrases=load_json(root/'references/phrases.json')
        required={'id','phrase','aliases','category','context_cue','likely_action','alternative','avoid','minimum_output','question'}
        if len(phrases)!=60:errors.append('此版本应包含60条词库规则')
        seen=set()
        for row in phrases:
            if not required.issubset(row):errors.append('词条缺少必填字段');continue
            if row['id'] in seen:errors.append('重复词条ID，'+row['id'])
            seen.add(row['id'])
            if not isinstance(row['aliases'],list):errors.append('词条 aliases 必须是列表')
            if any(not isinstance(row[k],str) or not row[k].strip() for k in required-{'aliases'}):errors.append('词条有空值或错误类型')
        entries=load_json(root/'examples/manifest.json')
        if len(entries)!=8:errors.append('此版本应包含8个参考案例')
        case_ids=set()
        for entry in entries:
            if entry['id'] in case_ids:errors.append('重复案例ID')
            case_ids.add(entry['id'])
            ip=(root/'examples'/entry['input']).resolve()
            op=(root/'examples'/entry['reference_output']).resolve()
            if not ip.is_relative_to(root/'examples') or not op.is_relative_to(root/'examples'):
                errors.append('案例路径越界');continue
            if hashlib.sha256(ip.read_bytes()).hexdigest()!=entry['input_sha256']:errors.append('输入已变化，请检查案例并更新 manifest，'+entry['id'])
            data=load_json(op)
            errors += [entry['id']+'，'+x for x in validate_package(data,op.parent)]
            if op.with_suffix('.md').read_text(encoding='utf-8')!=render_markdown(data):errors.append('Markdown 与参考 JSON 不一致，'+entry['id'])
            if entry.get('live_model_run') is not False:errors.append('参考案例不得冒称独立模型运行')
        evals=load_json(root/'eval/cases.json')
        if len(evals)!=16 or len({x['id'] for x in evals})!=16:errors.append('评估场景应有16个唯一ID')
        if any(x.get('run_status')!='not-run' for x in evals):errors.append('本次发布的额外评估场景应标为未运行')
        sources=load_json(root/'docs/research/sources.json')
        if len(sources)!=7:errors.append('此版本应记录7个竞品来源')
        from run_demo import build_html,load_cases
        if (root/'docs/demo/index.html').is_file():
            if (root/'docs/demo/index.html').read_text(encoding='utf-8')!=build_html(load_cases(root)):
                errors.append('离线页面需要从当前参考案例重新生成')
    except (OSError,ValueError,UnicodeError,KeyError,TypeError) as exc:
        errors.append('资源检查失败，'+str(exc))
    return errors


def main() -> int:
    errors=check_repo(ROOT)
    if errors:
        print('\n'.join(errors),file=sys.stderr);return 1
    print('PASS，入口、Python 3.10语法、JSON、内部链接、60条规则、8个参考案例、16个待测场景及7个来源已检查。')
    print('仅本地静态与参考示例校验，未验证宿主模型行为或外部链接当前可达性。')
    return 0

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
