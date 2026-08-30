"""CLI 端到端：文件进、册出、失败退出非零。"""

from __future__ import annotations

import json
from pathlib import Path

from reportrender.cli import main
from tests.support import ITEM_LABELS, LOCKED_TEXTS_JSON, PACKAGE_JSON, PAGES_JSON


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    pages = tmp_path / "pages.json"
    package = tmp_path / "package.json"
    locked = tmp_path / "locked.json"
    items = tmp_path / "anchor_items.json"
    pages.write_text(json.dumps(PAGES_JSON, ensure_ascii=False), encoding="utf-8")
    package.write_text(json.dumps(PACKAGE_JSON, ensure_ascii=False), encoding="utf-8")
    locked.write_text(json.dumps(LOCKED_TEXTS_JSON, ensure_ascii=False), encoding="utf-8")
    # contracts registries/anchor_items.json 的形态：{"items": {kind: {项名: {"label": …}}}}
    items.write_text(
        json.dumps(
            {"items": {k: {n: {"label": v} for n, v in t.items()} for k, t in ITEM_LABELS.items()}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return pages, package, locked, items


def test_cli_renders_book(tmp_path: Path) -> None:
    pages, package, locked, items = _write_inputs(tmp_path)
    out = tmp_path / "book.html"
    code = main(
        [
            "--pages",
            str(pages),
            "--package",
            str(package),
            "--locked-texts",
            str(locked),
            "--anchor-items",
            str(items),
            "-o",
            str(out),
        ]
    )
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert "装修设计报告" in html


def test_cli_without_locked_texts_still_renders(tmp_path: Path) -> None:
    pages, package, _, items = _write_inputs(tmp_path)
    out = tmp_path / "book.html"
    assert (
        main(
            [
                "--pages",
                str(pages),
                "--package",
                str(package),
                "--anchor-items",
                str(items),
                "-o",
                str(out),
            ]
        )
        == 0
    )
    # 全部文案缺席=少说，不是失败；正文里不得出现任何编造的文案
    assert "现场确认并勾选" not in out.read_text(encoding="utf-8")


def test_cli_fails_loud_on_bad_placeholder(tmp_path: Path) -> None:
    pages, package, locked, items = _write_inputs(tmp_path)
    broken = json.loads(pages.read_text(encoding="utf-8"))
    broken[0]["cards"][0]["body"] = "见 {lkp-ghost}"
    pages.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "book.html"
    code = main(
        [
            "--pages",
            str(pages),
            "--package",
            str(package),
            "--locked-texts",
            str(locked),
            "--anchor-items",
            str(items),
            "-o",
            str(out),
        ]
    )
    assert code == 2
    assert not out.exists()  # 失败不落盘：不出半册


def test_cli_without_anchor_items_fails_loud_on_open_set_items(tmp_path: Path) -> None:
    """开集项名的展示名不在包里、在受控词表里——没传词表就渲不出，而不是猜一个中文名。

    这条守的是"缺是渲不出不是猜"：展示名一旦允许兜底（印项名、印空），业主看到的就是内部标识符
    或半句话。它与"锁定文案缺席=少说"是同一条纪律的两个方向——文案缺可以少说，展示名缺不能瞎说。
    """
    pages, package, locked, _ = _write_inputs(tmp_path)
    out = tmp_path / "book.html"
    code = main(
        [
            "--pages",
            str(pages),
            "--package",
            str(package),
            "--locked-texts",
            str(locked),
            "-o",
            str(out),
        ]
    )
    assert code == 2
    assert not out.exists()
