"""整册渲染红线：内部编号不出户、锁定文案逐字与缺席、标注按名 join、匿名解析守卫。"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from pydantic import ValidationError

from reportrender.anchor_text import RenderError
from reportrender.models import RenderPackage, parse_pages
from reportrender.render import render_book
from tests.support import ITEM_LABELS, LOCKED_TEXTS_JSON, PACKAGE_JSON, PAGES_JSON


def _render(
    pages_json: list[dict[str, Any]] | None = None,
    package_json: dict[str, Any] | None = None,
    locked: dict[str, str] | None = None,
) -> Any:
    pages = parse_pages(copy.deepcopy(pages_json or PAGES_JSON))
    package = RenderPackage.model_validate(copy.deepcopy(package_json or PACKAGE_JSON))
    return render_book(pages, package, LOCKED_TEXTS_JSON if locked is None else locked, ITEM_LABELS)


def test_book_renders_cards_with_values() -> None:
    result = _render()
    assert result.page_count == 3
    assert result.card_count == 4
    # 单值场合只出数：边界说法与单位都在写手那句话里（用户裁决 2026-08-30 晚）
    assert "900–950" in result.html
    assert "60–68" in result.html
    # 封面基准日来自数据包，不来自时钟
    assert "2026-08-29" in result.html


def test_lighting_chapter_renders_whole_and_item_references() -> None:
    # 灯光分场景照度：v2.8 前本层直接 fail loud，整册出不来
    html = _render().html
    assert "一般活动 100 lx、书写阅读 300 lx" in html  # 整条引用
    assert "读书位单独加亮到 300 lx" in html  # 单项引用：本层出 300，lx 是写手写的
    assert "reading" not in html and "general" not in html


def test_reference_plane_stays_off_paper() -> None:
    # 参考平面本轮解析但不上纸（形态与挂载位待定，见 anchor_text 模块 docstring）
    assert "0.75m 水平面" not in _render().html


def test_book_is_readable_on_a_phone() -> None:
    # 业主在 IM 里点开链接，第一现场是手机：缺 viewport 声明则整页按 980px 版面缩放，
    # 11pt 正文缩到看不清；屏幕侧还要有自己的留白，否则正文顶着屏幕边缘。
    html = _render().html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert "@media screen" in html


def test_no_internal_ids_in_output() -> None:
    assert "lkp-" not in _render().html


def test_chapter_titles_are_display_names() -> None:
    html = _render().html
    assert "人体工学" in html
    assert "造价" in html
    assert "ergonomics" not in html


def test_locked_text_verbatim_and_absence() -> None:
    result = _render()
    # 有正文的逐字出现（禁改写禁拼接：独立成块）
    assert "请在水电交底当天，携带本清单与施工方逐项现场确认并勾选。" in result.html
    # 待补录的缺席 + 记录（缺是少说，编是替企业作错误承诺）
    assert ("page-ergonomics", "DISCLAIM_PRICE") in result.missing_locked_texts
    assert "DISCLAIM_PRICE" not in result.html


def test_provenance_footer_structured_fields_only() -> None:
    html = _render().html
    assert "本页依据" in html
    assert "橱柜台面高" in html  # 名称从数据包 join，不打印 lkp_id
    assert "已校准" in html and "未校准" in html
    assert "2026-08-27 至 2026-11-27" in html  # 取数时间原样出（时效资产）
    # 来源列整列待裁（真跑立案：source 是审计叙事非客户引文），暂不上纸
    assert "行业通行" not in html
    assert "市场行情采集" not in html


def test_note_referencing_unknown_anchor_fails() -> None:
    pages = copy.deepcopy(PAGES_JSON)
    pages[0]["provenance_notes"][0]["lkp_id"] = "lkp-ghost"
    with pytest.raises(RenderError, match="不存在"):
        _render(pages_json=pages)


def test_unknown_top_level_field_rejected() -> None:
    # 匿名结构守卫：任何多出来的字段（哪怕叫别的名）都拒绝解析
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["ownerName"] = "张三"
    with pytest.raises(ValidationError):
        RenderPackage.model_validate(pkg)


def test_withheld_anchors_nonempty_rejected() -> None:
    # v2.4 作废字段恒空：非空=生产方还在隐藏档，整包失败是故意的严
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["withheldAnchors"] = [{"lkpId": "lkp-x", "basisTag": "a@v1", "reason": "no_range_form"}]
    with pytest.raises(ValidationError):
        RenderPackage.model_validate(pkg)


def test_unmapped_domain_renders_with_warning() -> None:
    pages = copy.deepcopy(PAGES_JSON)
    pages[1]["domain"] = "storage"
    result = _render(pages_json=pages)
    assert any("storage" in w for w in result.warnings)
