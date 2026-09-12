"""离线结构检查与 Markdown 渲染，不执行任务，也不推断经理意图。"""
from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2 * 1024 * 1024


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'JSON 存在重复键 {key}')
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('文件超过 2 MiB，请缩小输入。')
    return json.loads(path.read_text(encoding='utf-8-sig'), object_pairs_hook=_unique_object,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f'非法 JSON 数值 {x}')))


def schema_errors(value: Any, schema: dict[str, Any], path: str = '$') -> list[str]:
    """只实现本仓库 schema 所使用的关键词，不是通用 JSON Schema 引擎。"""
    out: list[str] = []
    kind = schema.get('type')
    ok = {'object': lambda: isinstance(value, dict),
          'array': lambda: isinstance(value, list),
          'string': lambda: isinstance(value, str),
          'boolean': lambda: type(value) is bool,
          'integer': lambda: type(value) is int}
    if kind not in ok:
        return [f'SCHEMA_DEFINITION {path} 不支持类型 {kind}']
    if not ok[kind]():
        return [f'SCHEMA {path} 必须为 {kind}']
    if 'const' in schema and value != schema['const']:
        out.append(f'SCHEMA {path} 必须为 {schema["const"]}')
    if 'enum' in schema and value not in schema['enum']:
        out.append(f'SCHEMA {path} 不在允许值中')
    if kind == 'object':
        props = schema.get('properties', {})
        for key in schema.get('required', []):
            if key not in value:
                out.append(f'SCHEMA {path}.{key} 缺失')
        for key, item in value.items():
            if key in props:
                out.extend(schema_errors(item, props[key], f'{path}.{key}'))
            elif schema.get('additionalProperties') is False:
                out.append(f'SCHEMA {path}.{key} 未知字段')
    elif kind == 'array':
        if len(value) < schema.get('minItems', 0):
            out.append(f'SCHEMA {path} 条目不足')
        for i, item in enumerate(value):
            out.extend(schema_errors(item, schema['items'], f'{path}[{i}]'))
    elif kind == 'string':
        if len(value.strip()) < schema.get('minLength', 0):
            out.append(f'SCHEMA {path} 不得为空')
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            out.append(f'SCHEMA {path} 格式不符')
    elif kind == 'integer':
        if value < schema.get('minimum', value) or value > schema.get('maximum', value):
            out.append(f'SCHEMA {path} 超出范围')
    return out


def validate_package(data: Any, source_root: Path | None = None) -> list[str]:
    errors = schema_errors(data, load_json(ROOT / 'assets' / 'work-package.schema.json'))
    if errors:
        return errors
    for group in ('evidence', 'assumptions', 'clarifications', 'deliverables', 'tasks', 'approval_gates'):
        ids = [x['id'] for x in data[group]]
        if len(ids) != len(set(ids)):
            errors.append(f'DUPLICATE_ID {group} 有重复编号')
    evidence = {x['id']: x for x in data['evidence']}
    tasks = {x['id']: x for x in data['tasks']}
    deliverables = {x['id']: x for x in data['deliverables']}
    for group in ('facts', 'interpretations', 'deliverables', 'approval_gates', 'risks'):
        for i, row in enumerate(data[group]):
            for ref in row['evidence_ids']:
                if ref not in evidence:
                    errors.append(f'EVIDENCE_REF {group}[{i}] 引用了不存在的 {ref}')
    for row in data['evidence']:
        if row['source'] == 'input.request':
            if row['quote'] not in data['request']:
                errors.append(f'QUOTE_MISMATCH {row["id"]} 不是原话中的逐字片段')
        elif source_root is not None:
            root = source_root.resolve()
            raw = row['source']
            # Reject Windows drives and traversal on every platform, not only Windows.
            rel = Path(raw.replace('\\', '/'))
            target = (root / rel).resolve()
            if rel.is_absolute() or ':' in raw or '..' in rel.parts or not target.is_relative_to(root):
                errors.append(f'SOURCE_PATH {row["id"]} 资料路径超出授权目录')
                continue
            if not target.is_file():
                errors.append(f'SOURCE_MISSING {row["id"]} 无法读取 {raw}')
                continue
            if target.suffix.lower() not in ('.md', '.txt', '.csv', '.json'):
                errors.append(f'SOURCE_TYPE {row["id"]} 请先用宿主工具提取为文本')
                continue
            try:
                if target.stat().st_size > MAX_BYTES:
                    raise ValueError('资料超过 2 MiB')
                text = target.read_text(encoding='utf-8-sig')
                if row['quote'] not in text:
                    errors.append(f'QUOTE_MISMATCH {row["id"]} 引文未在 {raw} 中找到')
            except (OSError, ValueError, UnicodeError) as exc:
                errors.append(f'SOURCE_READ {row["id"]} {exc}')
    if sum(x['selected'] for x in data['interpretations']) != 1:
        errors.append('INTERPRETATION 必须且只能选择一个暂定解释')
    policy = data['question_policy']
    if len(data['clarifications']) > policy['budget']:
        errors.append('QUESTION_BUDGET 实际问题数超过设定预算')
    if policy['budget'] > 2 and not (policy['exception_reason'].strip() and data['approval_gates']):
        errors.append('QUESTION_EXCEPTION 超过两个问题需写明高风险原因和审批门槛')
    for x in data['assumptions']:
        if not x['reversible']:
            errors.append(f'IRREVERSIBLE_ASSUMPTION {x["id"]} 不可逆决策应列为待确认门槛')
        if x['risk'] == 'high':
            errors.append(f'HIGH_RISK_ASSUMPTION {x["id"]} 高风险事项不得作为默认假设')
    blocks: set[str] = set()
    for group in ('clarifications', 'approval_gates'):
        for row in data[group]:
            for tid in row['blocks']:
                if tid not in tasks:
                    errors.append(f'TASK_REF {row["id"]} 引用了不存在的 {tid}')
            if group == 'approval_gates' and row['confirmed']:
                if not row['evidence_ids']:
                    errors.append(f'APPROVAL_EVIDENCE {row["id"]} 缺少授权证据')
            else:
                blocks.update(row['blocks'])
    seen: set[str] = set()
    waiting: set[str] = set()
    for row in data['tasks']:
        tid = row['id']
        if row['deliverable_id'] not in deliverables:
            errors.append(f'DELIVERABLE_REF {tid} 交付物不存在')
        if any(dep not in seen for dep in row['depends_on']):
            errors.append(f'TASK_DEPENDENCY {tid} 依赖必须位于当前任务之前，不能成环')
        blocked_dep = any(dep in waiting for dep in row['depends_on'])
        if tid in blocks and row['state'] == 'ready':
            errors.append(f'GATE_BYPASS {tid} 未解除的门槛不能标为可执行')
        if blocked_dep and row['state'] == 'ready':
            errors.append(f'DEPENDENCY_BYPASS {tid} 依赖仍在等待')
        if row['state'] == 'waiting':
            waiting.add(tid)
            if tid not in blocks and not blocked_dep:
                errors.append(f'UNEXPLAINED_WAIT {tid} 缺少等待原因或前置依赖')
        seen.add(tid)
    ready = sum(x['state'] == 'ready' for x in data['tasks'])
    expected = 'blocked' if ready == 0 else ('ready' if ready == len(data['tasks']) else 'partial')
    if data['execution_status'] != expected:
        errors.append(f'STATUS 应为 {expected}，与任务状态不一致')
    for row in data['deliverables']:
        if row['status'] == 'confirmed' and not row['evidence_ids']:
            errors.append(f'CONFIRMED_DELIVERABLE {row["id"]} 缺少明确要求的证据')
    return errors


def _safe(text: str) -> str:
    # Keep generated Markdown from embedding active HTML or invisible bidi controls.
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for ch in ('\u202a','\u202b','\u202d','\u202e','\u202c','\u2066','\u2067','\u2068','\u2069'):
        text = text.replace(ch, '')
    return text


def render_markdown(d: dict[str, Any]) -> str:
    """只渲染已由调用者校验过的对象。"""
    status = {'ready':'可先开工','partial':'部分可开工，部分等待确认','blocked':'暂不能开工'}
    lines = ['# heihua-skill 工作包', '', '## 我理解的任务', '', _safe(d['task_understanding']), '',
             '当前状态，' + status[d['execution_status']] + '。', '', '## 已明确的信息', '']
    for row in d['facts']:
        lines.append('- ' + _safe(row['text']) + ' 依据 ' + '，'.join(row['evidence_ids']) + '。')
    lines += ['', '## 候选解释', '']
    for row in d['interpretations']:
        label = '暂按此推进' if row['selected'] else '保留的其他解释'
        confidence = {'high':'较高','medium':'中等','low':'较低'}[row['confidence']]
        lines += [f'- {label}，{_safe(row["meaning"])} 置信程度{confidence}。',
                  '  改变条件，' + _safe(row['would_change'])]
    lines += ['', '## 默认假设', '']
    if not d['assumptions']: lines.append('不需要新增可逆假设。')
    for row in d['assumptions']:
        lines += [f'- {row["id"]}，{_safe(row["text"])}',
                  '  复核节点，' + _safe(row['check_at']) + ' 退路，' + _safe(row['fallback'])]
    lines += ['', '## 预计交付物与验收', '']
    for row in d['deliverables']:
        label = '明确要求' if row['status'] == 'confirmed' else '建议，尚未确认'
        lines += [f'### {row["id"]} {_safe(row["name"])}', '', f'形式，{_safe(row["format"])}。{label}。']
        lines.extend('- ' + _safe(x) for x in row['acceptance'])
        lines.append('')
    lines += ['## 执行顺序', '']
    for row in d['tasks']:
        state = '可执行' if row['state'] == 'ready' else '待确认后执行'
        deps = '，'.join(row['depends_on']) or '无'
        lines += [f'### {row["id"]} {_safe(row["action"])}', '',
                  f'状态，{state}。依赖，{deps}。对应交付物，{row["deliverable_id"]}。',
                  '时间安排，' + _safe(row['timebox'])]
        lines.extend('- 验收，' + _safe(x) for x in row['acceptance'])
        lines.append('')
    lines += ['## 需要确认的最少问题', '']
    if not d['clarifications']: lines.append('本轮不追加问题。不代表待审批事项已经获批。')
    for row in d['clarifications']:
        lines += [f'- {row["id"]}，{_safe(row["question"])}',
                  '  为什么问，' + _safe(row['why_needed']),
                  '  答案会改变，' + _safe(row['changes']),
                  '  暂无回复时，' + _safe(row['if_no_answer'])]
    if d['approval_gates']:
        lines += ['', '## 不能跳过的确认门槛', '']
        for row in d['approval_gates']:
            label = '已有证据确认' if row['confirmed'] else '仍未确认'
            lines.append(f'- {row["id"]}，{_safe(row["reason"])} {label}，影响 ' + '，'.join(row['blocks']) + '。')
    lines += ['', '## 返工风险', '']
    if not d['risks']: lines.append('暂未识别出额外返工风险，仍需人工复核。')
    for row in d['risks']:
        lines.append('- ' + _safe(row['risk']) + ' 影响，' + _safe(row['impact']) + ' 处理，' + _safe(row['mitigation']))
    lines += ['', '## 本轮不做', ''] + ['- '+_safe(x) for x in d['out_of_scope']]
    lines += ['', '## 给上级的回复草稿', '', _safe(d['reply_draft']), '',
              '## 做到这里就停', '', _safe(d['stop_condition']), '', '## 依据索引', '']
    for row in d['evidence']:
        lines += [f'- {row["id"]}，{_safe(row["source"])}', '  原文片段，' + _safe(row['quote'])]
    lines += ['', '此工作包不代表负责人已批准，不会自动发送消息或执行所列任务。', '']
    return '\n'.join(lines)
