#!/usr/bin/env python3
"""heihua-skill 本地辅助工具。运行 --help 查看边界。"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
from work_package import ROOT, load_json, validate_package, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='离线词库检索、工作包校验与渲染，不调用模型，不自动生成任意任务的解码。')
    commands = parser.add_subparsers(dest='command', required=True)
    lookup = commands.add_parser('lookup', help='按字面子串检索候选规则，不做语义判断')
    lookup.add_argument('phrase')
    for name in ('check', 'render'):
        cmd = commands.add_parser(name)
        cmd.add_argument('input', type=Path)
        cmd.add_argument('--source-root', type=Path, help='仅检查此目录内 UTF-8 文本的逐字引用')
        if name == 'render':
            cmd.add_argument('--output', type=Path)
            cmd.add_argument('--force', action='store_true', help='允许覆盖指定输出，不允许覆盖输入')
    args = parser.parse_args(argv)
    try:
        if args.command == 'lookup':
            query = args.phrase.strip()
            if not query:
                raise ValueError('检索词不能为空')
            rows = load_json(ROOT / 'references' / 'phrases.json')
            hits = [x for x in rows if any(query in t or t in query for t in [x['phrase'], *x['aliases']])]
            if not hits:
                print('未匹配词条，请由宿主模型结合上下文解释，不要编造字典释义。')
                return 0
            print('以下只是候选解释，不能替代具体上下文。')
            for row in hits[:8]:
                print(f'\n{row["id"]} {row["phrase"]}\n场景线索，{row["context_cue"]}\n候选一，{row["likely_action"]}\n候选二，{row["alternative"]}\n避免，{row["avoid"]}\n最低交付，{row["minimum_output"]}\n需要时确认，{row["question"]}')
            return 0
        data = load_json(args.input)
        errors = validate_package(data, args.source_root)
        if errors:
            print('\n'.join(errors), file=sys.stderr)
            return 1
        if args.command == 'check':
            print('PASS，结构和声明的约束检查通过。不证明意图推断或授权内容真实。')
            return 0
        result = render_markdown(data)
        if args.output:
            if args.output.resolve() == args.input.resolve():
                raise ValueError('输出不能覆盖输入文件')
            if args.output.exists() and not args.force:
                raise ValueError('输出已存在，换一个路径或显式使用 --force')
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result, encoding='utf-8')
            print('已生成 ' + str(args.output))
        else:
            print(result, end='')
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        print(f'INPUT，{exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
