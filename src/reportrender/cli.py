"""CLI：`reportrender --pages pages.json --package package.json -o book.html`。

工具形态先行（裁决 2026-08-29：不成服务，以工具形式存在，后续报告产出上线时建立服务）——
本入口就是"工具"的全部：读入、渲染、落盘、汇报，失败带明细退出非零。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from reportrender.anchor_text import RenderError
from reportrender.models import (
    RenderPackage,
    parse_anchor_items,
    parse_locked_texts,
    parse_pages,
)
from reportrender.render import render_book


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="reportrender",
        description="报告渲染：pages + 报告数据包 → 单册自包含 HTML（确定性、零 LLM）",
    )
    parser.add_argument("--pages", required=True, type=Path, help="pages JSON（装配产物）")
    parser.add_argument("--package", required=True, type=Path, help="报告数据包 JSON")
    parser.add_argument(
        "--locked-texts",
        type=Path,
        default=None,
        help="锁定文案数据 JSON（{ID: 正文}）；缺省=全部按待补录缺席",
    )
    parser.add_argument(
        "--anchor-items",
        type=Path,
        default=None,
        help=(
            "落点项名受控词表 JSON（contracts registries/anchor_items.json）："
            "开集两类（分场景/分项）并列多项时的展示名。缺省=空表，这两类的整条引用即 fail loud"
        ),
    )
    parser.add_argument("-o", "--out", type=Path, default=Path("report.html"))
    args = parser.parse_args(argv)

    try:
        pages = parse_pages(_load_json(args.pages))
        package = RenderPackage.model_validate(_load_json(args.package))
        locked = parse_locked_texts(_load_json(args.locked_texts)) if args.locked_texts else {}
        items = parse_anchor_items(_load_json(args.anchor_items)) if args.anchor_items else {}
        result = render_book(pages, package, locked, items)
    except RenderError as e:
        print("渲染失败（fail loud，不空替不静默跳过）：", file=sys.stderr)
        for line in e.details:
            print(f"  - {line}", file=sys.stderr)
        return 2
    except (ValueError, OSError) as e:
        print(f"输入解析失败：{e}", file=sys.stderr)
        return 2

    args.out.write_text(result.html, encoding="utf-8")
    print(f"已出册：{args.out}（{result.page_count} 页 / {result.card_count} 卡）")
    for page_id, text_id in result.missing_locked_texts:
        # 缺是少说（正文待补录，禁编造），但缺了多少必须让人看见。
        print(f"锁定文案缺席：页 {page_id} 要求 {text_id}（待补录，未渲出）", file=sys.stderr)
    for warning in result.warnings:
        print(f"警告：{warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
