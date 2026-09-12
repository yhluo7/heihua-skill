#!/usr/bin/env python3
"""复制运行所需文件。默认仅预览，--apply 才写入，不覆盖现有安装。"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
ITEMS=('SKILL.md','LICENSE','references','assets','scripts','agents')

def install_skill(source: Path,destination: Path,apply: bool=False) -> list[str]:
    if not (source/'SKILL.md').is_file():
        raise ValueError('源目录缺少 SKILL.md')
    if destination.name!='heihua-skill':
        raise ValueError('安装目录末级必须为 heihua-skill')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('目标已存在，不覆盖。请先人工备份或移走旧安装。')
    for parent in destination.parents:
        if parent.is_symlink():
            raise ValueError('目标路径含符号链接，请使用真实路径并核对权限。')
    for item in ITEMS:
        if not (source/item).exists():
            raise ValueError('源目录缺少 '+item)
    paths=[str(destination/x) for x in ITEMS]
    if not apply:
        return paths
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.heihua-install-',dir=destination.parent))
    try:
        for item in ITEMS:
            src=source/item
            if src.is_dir():
                shutil.copytree(src,staging/item,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            else:
                shutil.copy2(src,staging/item)
        if destination.exists():
            raise FileExistsError('复制期间目标被创建，已停止安装。')
        staging.rename(destination)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return paths


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',choices=('codex','claude'),required=True)
    parser.add_argument('--scope',choices=('user','project'),default='user')
    parser.add_argument('--project',type=Path,default=Path.cwd())
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    root=Path.home() if args.scope=='user' else args.project.resolve()
    directory='.agents' if args.target=='codex' else '.claude'
    dest=root/directory/'skills'/'heihua-skill'
    try:
        files=install_skill(ROOT,dest,args.apply)
        print(('已安装。' if args.apply else '仅预览，没有写入。加 --apply 后执行。')+'\n目标，'+str(dest))
        if not args.apply:print('\n'.join(files))
        return 0
    except (OSError,ValueError) as exc:
        print(str(exc),file=sys.stderr);return 1

if __name__=='__main__':
    if hasattr(sys.stdout,'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8');sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
