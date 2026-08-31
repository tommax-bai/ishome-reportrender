"""记号替换红线：七类 valueKind 各渲各样、单项引用只出值、之外 fail loud、数字原样不换算。"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from reportrender.anchor_text import (
    RenderError,
    format_anchor_item,
    format_anchor_value,
    replace_placeholders,
)
from reportrender.models import RenderPackage, ReportAnchor
from tests.support import ITEM_LABELS, PACKAGE_JSON


def _anchors() -> dict[str, ReportAnchor]:
    return RenderPackage.model_validate(copy.deepcopy(PACKAGE_JSON)).anchors_by_id()


def _with_value(lkp_id: str, **overrides: Any) -> ReportAnchor:
    """改一条落点的 valueKind/value/unit 再解析——形态测试用。"""
    pkg = copy.deepcopy(PACKAGE_JSON)
    for anchor in pkg["anchors"]:
        if anchor["lkpId"] == lkp_id:
            anchor.update(overrides)
    return RenderPackage.model_validate(pkg).anchors_by_id()[lkp_id]


# ---------------------------------------------------------------------------
# 整条引用：七类各一
# ---------------------------------------------------------------------------


def test_single_and_range_forms() -> None:
    anchors = _anchors()
    # single = 一个匿名项，值是数
    # 单值场合出**裸数**：单位由写手照抄下发的那个字（用户裁决 2026-08-30 晚）
    assert format_anchor_value(anchors["lkp-wardrobe-rod"], ITEM_LABELS) == "2136"
    # range = 一个匿名项，值是区间；**只给一侧时出裸值**——一个记号只渲一个值，
    # 写手的句子就在它旁边，边界说法归句子（用户裁决 2026-08-30）
    assert format_anchor_value(anchors["lkp-counter-height"], ITEM_LABELS) == "900–950"
    assert format_anchor_value(anchors["lkp-passage-main"], ITEM_LABELS) == "900"
    assert format_anchor_value(anchors["lkp-price-hydro-labor"], ITEM_LABELS) == "60–68"


def test_scenario_form() -> None:
    # 分场景（受控词表序）：单位逐项各带
    assert (
        format_anchor_value(_anchors()["lkp-illuminance-living"], ITEM_LABELS)
        == "一般活动 100 lx、书写阅读 300 lx"
    )


def test_tier_form_uses_closed_set_order() -> None:
    # 档位闭集序 低→中→高，与数据包里的键序（high/low/medium）无关
    assert (
        format_anchor_value(_anchors()["lkp-budget-confidence-width"], ITEM_LABELS)
        == "低档 0.5、中档 0.3、高档 0.15"
    )


def test_dimension_form_keeps_axis_labels() -> None:
    """并列多项**仍由本层带边界措辞**：句子够不着一个记号里面的每一项。

    与上面单值场合出裸值对照——同一条纪律的两侧（用户裁决 2026-08-30："在输入的地方给出
    需要填的值的特征"，而并列场合写手无从逐项给特征）。
    """
    assert (
        format_anchor_value(_anchors()["lkp-shower-clear"], ITEM_LABELS)
        == "宽不低于 800 mm、深不低于 800 mm"
    )


def test_component_form_keeps_ratio_verbatim() -> None:
    # 分项：0.03 原样出，不擅自变 3%（禁换算折算）。
    # **本仓夹具刻意不跟着改源那一批走**：真种子 2026-08-31 已改成百分数（80 + unit %），
    # 而这条断言守的是"本层不许自己换算"——留一条小数在这儿，换算真发生了它当场红。
    assert (
        format_anchor_value(_anchors()["lkp-budget-share"], ITEM_LABELS)
        == "主材 0.2–0.35、拆改 0.03–0.08"
    )


def test_percent_unit_sits_against_the_number() -> None:
    """符号类单位紧排：``60%`` 不是 ``60 %``；中文单位照旧留一格（见上面几条）。

    这是**排版不是换算**——值一个字没动。判据与射程（当前只到 ``%``）在
    :func:`reportrender.anchor_text.join_unit` 的注释里。
    """
    anchor = _with_value("lkp-budget-share", unit="%", value={"main-material": 20, "demolition": 3})
    assert format_anchor_value(anchor, ITEM_LABELS) == "主材 20%、拆改 3%"


def test_comparison_form_derives_label_from_tiers() -> None:
    # 档位比较：项名形态 {高档}-vs-{低档}，展示名由 tier 闭集派生
    assert (
        format_anchor_value(_anchors()["lkp-budget-tier-gap"], ITEM_LABELS)
        == "中档相对低档 1.3–1.8 倍、高档相对中档 1.4–2.2 倍"
    )


# ---------------------------------------------------------------------------
# 单项引用：只出那一项的值，项名（内部标识符）不出现在输出里
# ---------------------------------------------------------------------------


def test_item_reference_scalar() -> None:
    anchors = _anchors()
    assert format_anchor_item(anchors["lkp-illuminance-living"], "reading") == "300"
    out = replace_placeholders("读书位加亮到 {lkp-illuminance-living.reading} lx。", anchors)
    assert out == "读书位加亮到 300 lx。"
    assert "reading" not in out


def test_item_reference_range() -> None:
    anchors = _anchors()
    assert format_anchor_item(anchors["lkp-budget-share"], "main-material") == "0.2–0.35"
    # 按项引用＝一个记号只渲一个值，句子够得着 → 裸数（边界说法与单位都归句子）
    assert format_anchor_item(anchors["lkp-shower-clear"], "width") == "800"


# ---------------------------------------------------------------------------
# fail loud
# ---------------------------------------------------------------------------


def test_item_reference_on_anonymous_anchor_fails() -> None:
    # single/range 只有一个匿名项，不存在可引的项
    anchors = _anchors()
    with pytest.raises(RenderError, match="没有可引的项名"):
        format_anchor_item(anchors["lkp-wardrobe-rod"], "value")
    with pytest.raises(RenderError, match="没有可引的项名"):
        replace_placeholders("{lkp-counter-height.min}", anchors)


def test_unknown_item_name_reports_actual_items() -> None:
    with pytest.raises(RenderError) as e:
        format_anchor_item(_anchors()["lkp-illuminance-living"], "vanity")
    assert "该落点实际有：general、reading" in e.value.details[0]


def test_unregistered_item_label_fails() -> None:
    # 维度闭集外的轴（v2.8 前"高度轴未登记"那条测试的新形态）
    anchor = _with_value(
        "lkp-shower-clear", value={"width": {"min": 800}, "ceiling": {"min": 2000}}
    )
    with pytest.raises(RenderError, match="未登记展示名"):
        format_anchor_value(anchor, ITEM_LABELS)


def test_malformed_comparison_item_name_fails() -> None:
    anchor = _with_value("lkp-budget-tier-gap", value={"品质-vs-舒适": {"min": 1.4, "max": 2.2}})
    with pytest.raises(RenderError, match="不合档位比较形态"):
        format_anchor_value(anchor, ITEM_LABELS)


def test_unknown_value_form_fails_loud() -> None:
    # 项的值是数组（v2.8 前造价占比的真形态）：呈现是设计题不是替换题，失败上报待裁，不猜
    anchor = _with_value("lkp-budget-share", value={"main-material": [0.2, 0.35]})
    with pytest.raises(RenderError, match="值形态不认识"):
        format_anchor_value(anchor, ITEM_LABELS)


def test_mixed_keys_fail() -> None:
    # 元信息挤在 value 里（v2.8 前的 unit/plane 键）：min/max 之外的键即形态不认识
    anchor = _with_value("lkp-counter-height", value={"min": 900, "max": 950, "unit": "mm"})
    with pytest.raises(RenderError, match="值形态不认识"):
        format_anchor_value(anchor, ITEM_LABELS)


def test_value_kind_and_shape_must_agree() -> None:
    with pytest.raises(RenderError, match="声明 valueKind=single"):
        format_anchor_value(
            _with_value("lkp-wardrobe-rod", value={"min": 900, "max": 950}), ITEM_LABELS
        )
    with pytest.raises(RenderError, match="声明 valueKind=range"):
        format_anchor_value(_with_value("lkp-counter-height", value=900), ITEM_LABELS)
    with pytest.raises(RenderError, match="值却不是「项名 → 值」映射"):
        format_anchor_value(_with_value("lkp-illuminance-living", value=100), ITEM_LABELS)


def test_non_numeric_value_fails() -> None:
    anchor = _with_value("lkp-counter-height", value={"min": "九百"})
    with pytest.raises(RenderError, match="非数字"):
        format_anchor_value(anchor, ITEM_LABELS)


def test_replace_keeps_number_verbatim() -> None:
    out = replace_placeholders("建议 {lkp-counter-height} mm。", _anchors())
    # 原样输出：mm 不折算 m，区间渲染成区间；单位是写手写的那个字，本层不碰
    assert out == "建议 900–950 mm。"


def test_unknown_placeholder_fails_with_all_missing() -> None:
    with pytest.raises(RenderError) as e:
        replace_placeholders("{lkp-ghost-a} 与 {lkp-ghost-b.reading}", _anchors())
    assert len(e.value.details) == 2  # 收齐一次报，不是碰到第一个就停
