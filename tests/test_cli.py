"""CLI 端到端：文件进、册出、失败退出非零。"""

from __future__ import annotations

import json
from pathlib import Path

from reportrender.cli import main
from tests.support import LOCKED_TEXTS_JSON, PACKAGE_JSON, PAGES_JSON


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    pages = tmp_path / "pages.json"
    package = tmp_path / "package.json"
    locked = tmp_path / "locked.json"
    pages.write_text(json.dumps(PAGES_JSON, ensure_ascii=False), encoding="utf-8")
    package.write_text(json.dumps(PACKAGE_JSON, ensure_ascii=False), encoding="utf-8")
    locked.write_text(json.dumps(LOCKED_TEXTS_JSON, ensure_ascii=False), encoding="utf-8")
    return pages, package, locked


def test_cli_renders_book(tmp_path: Path) -> None:
    pages, package, locked = _write_inputs(tmp_path)
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
    assert code == 0
    html = out.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert "装修设计报告" in html


def test_cli_without_locked_texts_still_renders(tmp_path: Path) -> None:
    pages, package, _ = _write_inputs(tmp_path)
    out = tmp_path / "book.html"
    assert main(["--pages", str(pages), "--package", str(package), "-o", str(out)]) == 0
    # 全部文案缺席=少说，不是失败；正文里不得出现任何编造的文案
    assert "现场确认并勾选" not in out.read_text(encoding="utf-8")


def test_cli_fails_loud_on_bad_placeholder(tmp_path: Path) -> None:
    pages, package, locked = _write_inputs(tmp_path)
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
            "-o",
            str(out),
        ]
    )
    assert code == 2
    assert not out.exists()  # 失败不落盘：不出半册
