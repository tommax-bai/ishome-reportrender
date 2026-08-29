"""占位符替换与落点值的文字形态。

红线（交接文档"渲染层的纪律"）：

- 数字**原样输出，禁换算折算**——mm 不折成 m、0.03 不擅自变 3%；值怎么来的怎么出。
- 一个占位符 = 整条落点：区间渲染成区间，不取中值、不挑一头。
- **fail loud**：占位符找不到落点、值形态不认识 → 抛 :class:`RenderError` 并报明细，
  不空替、不静默跳过（静默丢内容是漏拦的一种）。
- 首版只认三形态：``{min,max}`` 区间 / ``{v}`` 点值 / 单边界（只 min 或只 max）。
  其余形态（分档映射、嵌套结构）的呈现是设计题不是替换题，遇到即失败上报待裁，不猜。

单边界的措辞定为"不低于/不超过"（渲染的是边界语义，不是造数字）——这是首版的呈现选择，
记录在交接文档追记，用户可改判。
"""

from __future__ import annotations

import re

from reportrender.models import ReportAnchor

PLACEHOLDER_RE = re.compile(r"\{(lkp-[a-z0-9-]+)\}")

_ALLOWED_VALUE_KEYS = {"min", "max", "v"}


class RenderError(Exception):
    """渲染失败：details 逐条列明细，供 CLI 原样报出。"""

    def __init__(self, details: list[str]) -> None:
        self.details = details
        super().__init__("; ".join(details))


def _fmt_num(x: object, lkp_id: str) -> str:
    # bool 是 int 子类，先拦：True 当 1 输出属于值形态不认识，不属于数字。
    if isinstance(x, bool) or not isinstance(x, int | float):
        raise RenderError([f"落点 {lkp_id} 值非数字：{x!r}"])
    return str(x)


def format_anchor_value(anchor: ReportAnchor) -> str:
    """落点值 → 客户可读文字（含单位）。三形态之外一律 fail loud。"""
    keys = set(anchor.value)
    if not keys or not keys <= _ALLOWED_VALUE_KEYS:
        raise RenderError(
            [
                f"落点 {anchor.lkp_id} 值形态不认识（键：{sorted(keys)}）——"
                "首版只认 {min,max}/{v}/单边界，其余上报待裁，不猜"
            ]
        )
    v = anchor.value
    if keys == {"v"}:
        text = _fmt_num(v["v"], anchor.lkp_id)
    elif keys == {"min", "max"}:
        text = f"{_fmt_num(v['min'], anchor.lkp_id)}–{_fmt_num(v['max'], anchor.lkp_id)}"
    elif keys == {"min"}:
        text = f"不低于 {_fmt_num(v['min'], anchor.lkp_id)}"
    elif keys == {"max"}:
        text = f"不超过 {_fmt_num(v['max'], anchor.lkp_id)}"
    else:
        # v 与 min/max 混合：不是登记过的形态。
        raise RenderError([f"落点 {anchor.lkp_id} 值形态不认识（键：{sorted(keys)}）"])
    return f"{text} {anchor.unit}" if anchor.unit else text


def replace_placeholders(text: str, anchors_by_id: dict[str, ReportAnchor]) -> str:
    """正文占位符 → 落点值文字。未知占位符收齐后一次性报出（fail loud）。"""
    missing = sorted({m.group(1) for m in PLACEHOLDER_RE.finditer(text)} - anchors_by_id.keys())
    if missing:
        raise RenderError([f"占位符 {{{lkp}}} 在数据包 anchors 中无落点" for lkp in missing])
    return PLACEHOLDER_RE.sub(
        lambda m: format_anchor_value(anchors_by_id[m.group(1)]),
        text,
    )
