"""占位符替换红线：三形态各渲各样、之外 fail loud、数字原样不换算。"""

from __future__ import annotations

import copy

import pytest

from reportrender.anchor_text import RenderError, format_anchor_value, replace_placeholders
from reportrender.models import RenderPackage
from tests.support import PACKAGE_JSON


def test_range_point_and_bound_forms() -> None:
    anchors = RenderPackage.model_validate(PACKAGE_JSON).anchors_by_id()
    assert format_anchor_value(anchors["lkp-counter-height"]) == "900–950 mm"
    assert format_anchor_value(anchors["lkp-wardrobe-rod"]) == "2136 mm"
    assert format_anchor_value(anchors["lkp-passage-main"]) == "不低于 900 mm"
    assert format_anchor_value(anchors["lkp-price-hydro-labor"]) == "60–68 元/㎡"


def test_axis_bound_form() -> None:
    # 带轴单边界（"前缀边界"，真源=淋浴房内空 {min_w,min_d}）：逐轴出、单位各带
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["anchors"][0]["value"] = {"min_w": 800, "min_d": 800}
    anchors = RenderPackage.model_validate(pkg).anchors_by_id()
    assert format_anchor_value(anchors["lkp-counter-height"]) == "宽不低于 800 mm、深不低于 800 mm"


def test_axis_bound_unknown_axis_fails() -> None:
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["anchors"][0]["value"] = {"min_w": 800, "min_h": 2000}  # 高度轴未登记
    anchors = RenderPackage.model_validate(pkg).anchors_by_id()
    with pytest.raises(RenderError, match="值形态不认识"):
        format_anchor_value(anchors["lkp-counter-height"])


def test_unknown_value_form_fails_loud() -> None:
    # 分档映射（如置信→宽度）是设计题不是替换题：内联即违规，必须失败上报。
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["anchors"][0]["value"] = {"高": 1, "低": 2}
    anchors = RenderPackage.model_validate(pkg).anchors_by_id()
    with pytest.raises(RenderError, match="值形态不认识"):
        format_anchor_value(anchors["lkp-counter-height"])


def test_mixed_keys_fail() -> None:
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["anchors"][0]["value"] = {"v": 900, "max": 950}
    anchors = RenderPackage.model_validate(pkg).anchors_by_id()
    with pytest.raises(RenderError, match="值形态不认识"):
        format_anchor_value(anchors["lkp-counter-height"])


def test_non_numeric_value_fails() -> None:
    pkg = copy.deepcopy(PACKAGE_JSON)
    pkg["anchors"][0]["value"] = {"v": "九百"}
    anchors = RenderPackage.model_validate(pkg).anchors_by_id()
    with pytest.raises(RenderError, match="非数字"):
        format_anchor_value(anchors["lkp-counter-height"])


def test_replace_keeps_number_verbatim() -> None:
    anchors = RenderPackage.model_validate(PACKAGE_JSON).anchors_by_id()
    out = replace_placeholders("建议 {lkp-counter-height}。", anchors)
    # 原样输出：mm 不折算 m，区间渲染成区间
    assert out == "建议 900–950 mm。"


def test_unknown_placeholder_fails_with_all_missing() -> None:
    anchors = RenderPackage.model_validate(PACKAGE_JSON).anchors_by_id()
    with pytest.raises(RenderError) as e:
        replace_placeholders("{lkp-ghost-a} 与 {lkp-ghost-b}", anchors)
    assert len(e.value.details) == 2  # 收齐一次报，不是碰到第一个就停
