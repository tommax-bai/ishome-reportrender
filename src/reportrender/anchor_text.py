"""占位符替换与落点值的文字形态。

**两层模型**（《装修报告生成规则规范》规则 1.9，v2.8 裁决 2026-08-30）：

    一条落点 = 若干「项」；一项的值 = 一个数，或一个区间。

正文因此有两种引用写法：整条 ``{lkp-x}``、单项 ``{lkp-x.项名}``。``valueKind`` 七值闭集
随落点下发，**可引用性与呈现形态都由它判定，不靠推断键名**：``single``/``range`` 只有一个
匿名项（只能整条引用），其余五类是「项名 → 值」映射（两种写法都可以）。``min``/``max``
不是项而是项的值形态——``{lkp-x.min}`` 因此在语法上不存在，"引一端丢另一端"由结构堵死。

红线（交接文档"渲染层的纪律"）：

- 数字**原样输出，禁换算折算**——mm 不折成 m、0.03 不擅自变 3%；值怎么来的怎么出。
- 区间渲染成区间：不取中值、不挑一头。
- **fail loud**：占位符找不到落点、按项引用了只有匿名项的落点、项名不存在、值形态不认识
  → 抛 :class:`RenderError` 并报明细，不空替、不静默跳过（静默丢内容是漏拦的一种）。
- **内部标识符禁入输出**：``lkp-`` 编号如此，**项名同理**——渲染出去的是值，不是名。整条
  引用要并列多项时才需要项的中文展示名，故展示名逐项登记（见下），表外项名 fail loud。

七类的呈现形态（本模块唯一的设计自由度，逐类登记于 :func:`format_anchor_value`）：

===========  =====================================  ==========================
valueKind    形态                                    例
===========  =====================================  ==========================
single       ``值``                                  ``2136 mm``
range        ``值``（区间/单边界）                    ``900–950 mm``
scenario     ``标签 值`` 顿号并列                     ``一般活动 100 lx、阅读 300 lx``
tier         同上（闭集序 低→中→高）                  ``低档 0.5、中档 0.3、高档 0.15``
dimension    同上（闭集序 宽→深→高）                  ``宽不低于 800 mm、深不低于 800 mm``
component    同上（词表登记序）                       ``主材 0.2–0.35、拆改 0.03–0.08``
comparison   ``高档相对低档 值``（档名取自 tier 闭集）  ``高档相对中档 1.4–2.2 倍``
===========  =====================================  ==========================

单边界的措辞定为"不低于/不超过"（渲染的是边界语义，不是造数字）；多项并列时**单位逐项各带**
（沿用带轴单边界的既有形态），并列顺序取**登记表内的顺序**，不取数据包里的键序——键序是
序列化的偶然，登记序是确定的。

参考平面（``referencePlane``，规则 1.9 二把它从 ``value`` 里挪出来了）**本轮不上纸**，理由与
后续路径见交接文档追记：真数据里它仍是"多项挤一串"的复合字符串（``一般活动 0.75m 水平面；
化妆台 台面（★混合照明照度）``），上纸就得拆，拆就是改写；且它该挂在页脚标注区，而标注挂什么
由 pages 的 ``provenance_notes`` 决定，渲染层自行添加等于替成文线拿主意（不重判）。触发条件：
**参考平面在数据包里按项拆开（每项一个平面），或成文线在 pages 上给出挂载位**，本层即补渲染
与测试——与"来源列整列待裁"同一处置。
"""

from __future__ import annotations

import re

from reportrender.models import ReportAnchor

# 记号形态（规则 1.9 定死）：整条 {lkp-x}，单项 {lkp-x.项名}。
PLACEHOLDER_RE = re.compile(r"\{(lkp-[a-z0-9-]+)(?:\.([a-z0-9-]+))?\}")
# 项名形态（同上）：ASCII 小写 kebab-case，与落点标识同一套。
ITEM_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# 一项的值只有两种形态：一个数，或一个区间（单边界只给一侧）。
_BOUND_KEYS = frozenset({"min", "max"})
_BOUND_PHRASES = ("不低于", "不超过")

# 只有一个匿名项的两类：没有可引的项名，按项引用即 fail loud。
_ANONYMOUS_KINDS = frozenset({"single", "range"})

# 项名 → 中文展示名。**表内顺序即呈现顺序**。
# 闭集两类（tier/dimension）取值由规范定死；开集两类（scenario/component）走受控词表——
# 词表的权威载体在源侧（规则 1.7 三"项名 + 中文语义 + 首次出处"），本表是它的展示投影，
# 随源侧改名进词表而增登记。表外项名不猜中文名（猜=编造），fail loud。
_TIER_ITEMS = {"low": "低档", "medium": "中档", "high": "高档"}
_DIMENSION_ITEMS = {"width": "宽", "depth": "深", "height": "高"}
# 闭集两类的展示名留在本层：取值由规范定死（tier low/medium/high、dimension depth/width/height），
# 新增取值本就要改规范，改规范时顺手改这里，不会漂。
_CLOSED_ITEM_TABLES: dict[str, dict[str, str]] = {
    "tier": _TIER_ITEMS,
    "dimension": _DIMENSION_ITEMS,
}

# 开集两类（scenario/component）的展示名**不在本层存**——它是 contracts 受控词表的一列，
# 由调用方经 `--anchor-items` 传入（同锁定文案 `--locked-texts` 的既有形态）。
# 本层另存一份就是同一条词表两处各写一遍：源侧长出新词、这边忘了改，整册当场渲不出来。
_OPEN_ITEM_KINDS = frozenset({"scenario", "component"})

ItemLabels = dict[str, dict[str, str]]

# 档位比较的项名是**形态受控**而非闭集：{高档}-vs-{低档}，两侧档名取自 tier 闭集。
_COMPARISON_SEP = "-vs-"


class RenderError(Exception):
    """渲染失败：details 逐条列明细，供 CLI 原样报出。"""

    def __init__(self, details: list[str]) -> None:
        self.details = details
        super().__init__("; ".join(details))


def _fmt_num(x: object, ref: str) -> str:
    # bool 是 int 子类，先拦：True 当 1 输出属于值形态不认识，不属于数字。
    if isinstance(x, bool) or not isinstance(x, int | float):
        raise RenderError([f"{ref} 值非数字：{x!r}"])
    return str(x)


def _fmt_value(value: object, unit: str | None, ref: str) -> str:
    """一项的值 → 文字（含单位）。标量与区间之外一律 fail loud。"""
    if isinstance(value, dict):
        keys = set(value)
        if not keys or not keys <= _BOUND_KEYS:
            raise RenderError(
                [
                    f"{ref} 值形态不认识（键：{sorted(keys)}）——一项的值只能是一个数或一个"
                    "区间（min/max），其余上报待裁，不猜"
                ]
            )
        if keys == _BOUND_KEYS:
            text = f"{_fmt_num(value['min'], ref)}–{_fmt_num(value['max'], ref)}"
        elif keys == {"min"}:
            text = f"不低于 {_fmt_num(value['min'], ref)}"
        else:
            text = f"不超过 {_fmt_num(value['max'], ref)}"
    elif isinstance(value, bool) or not isinstance(value, int | float):
        raise RenderError(
            [
                f"{ref} 值形态不认识：{value!r}——一项的值只能是一个数或一个区间（min/max），"
                "其余上报待裁，不猜"
            ]
        )
    else:
        text = _fmt_num(value, ref)
    return f"{text} {unit}" if unit else text


def _item_display(
    kind: str, item_name: str, ref: str, item_labels: ItemLabels
) -> tuple[tuple[int, int], str]:
    """项名 → （呈现序, 中文展示名）。表外项名 fail loud。

    没有登记的展示名 = 只能把内部标识符印上纸，那是红线；猜一个中文名则是编造。
    """
    if kind == "comparison":
        high, sep, low = item_name.partition(_COMPARISON_SEP)
        if not sep or high not in _TIER_ITEMS or low not in _TIER_ITEMS:
            raise RenderError(
                [
                    f"{ref} 的项名 {item_name!r} 不合档位比较形态"
                    f"「{{高档}}{_COMPARISON_SEP}{{低档}}」——两侧档名须取自 "
                    f"{'/'.join(_TIER_ITEMS)}"
                ]
            )
        tiers = list(_TIER_ITEMS)
        order = (tiers.index(low), tiers.index(high))
        return order, f"{_TIER_ITEMS[high]}相对{_TIER_ITEMS[low]}"

    table = item_labels.get(kind, {}) if kind in _OPEN_ITEM_KINDS else _CLOSED_ITEM_TABLES[kind]
    if item_name not in table:
        raise RenderError(
            [
                f"{ref} 的项名 {item_name!r} 未登记展示名（{kind} 本次已传入："
                f"{'、'.join(table) or '空'}）——项名是内部标识符，没有展示名就渲不出去；"
                "开集两类的展示名在 contracts 受控词表里，经 --anchor-items 传入；"
                "补登记后再渲，不猜"
            ]
        )
    return (list(table).index(item_name), 0), table[item_name]


def _with_label(label: str, text: str) -> str:
    # 边界措辞紧接标签（"宽不低于 800 mm"，沿用既有形态），其余空格分隔（"阅读 300 lx"）。
    return f"{label}{text}" if text.startswith(_BOUND_PHRASES) else f"{label} {text}"


def format_anchor_value(anchor: ReportAnchor, item_labels: ItemLabels | None = None) -> str:
    """整条引用 ``{lkp-x}`` → 客户可读文字（含单位）。按 ``valueKind`` 逐类登记，之外 fail loud。

    ``item_labels`` = 开集两类的展示名（contracts 受控词表投影）。缺省空表：开集落点的整条引用
    因此 fail loud 并报明细——**缺是渲不出，不是猜一个中文名**（同锁定文案"缺是少说"的同一条纪律）。
    """
    ref = f"落点 {anchor.lkp_id}"
    kind = anchor.value_kind
    value = anchor.value

    if kind in _ANONYMOUS_KINDS:
        if kind == "single" and isinstance(value, dict):
            raise RenderError([f"{ref} 声明 valueKind=single，值却不是一个数：{value!r}"])
        if kind == "range" and not isinstance(value, dict):
            raise RenderError([f"{ref} 声明 valueKind=range，值却不是一个区间：{value!r}"])
        return _fmt_value(value, anchor.unit, ref)

    if not isinstance(value, dict) or not value:
        raise RenderError(
            [f"{ref} 声明 valueKind={kind}（多项），值却不是「项名 → 值」映射：{value!r}"]
        )

    labels = item_labels or {}
    items = [(*_item_display(kind, name, ref, labels), name, v) for name, v in value.items()]
    items.sort(key=lambda row: row[0])
    return "、".join(
        _with_label(label, _fmt_value(item_value, anchor.unit, f"{ref} 的项 {name!r}"))
        for _order, label, name, item_value in items
    )


def format_anchor_item(anchor: ReportAnchor, item_name: str) -> str:
    """单项引用 ``{lkp-x.项名}`` → **那一项的值**（含单位）。项名不出现在输出里。"""
    ref = f"落点 {anchor.lkp_id}"
    if not ITEM_NAME_RE.match(item_name):
        raise RenderError([f"{ref} 的项名 {item_name!r} 不合项名形态 ^[a-z][a-z0-9-]*$"])
    if anchor.value_kind in _ANONYMOUS_KINDS:
        raise RenderError(
            [
                f"{ref} 是 {anchor.value_kind}（一个匿名项，没有可引的项名），却被按项引用 "
                f"{{{anchor.lkp_id}.{item_name}}}——整条引用写 {{{anchor.lkp_id}}}"
            ]
        )
    value = anchor.value
    if not isinstance(value, dict):
        raise RenderError(
            [
                f"{ref} 声明 valueKind={anchor.value_kind}（多项），值却不是「项名 → 值」"
                f"映射：{value!r}"
            ]
        )
    if item_name not in value:
        raise RenderError([f"{ref} 没有项 {item_name!r}——该落点实际有：{'、'.join(value)}"])
    return _fmt_value(value[item_name], anchor.unit, f"{ref} 的项 {item_name}")


def render_reference(
    anchor: ReportAnchor, item_name: str | None, item_labels: ItemLabels | None = None
) -> str:
    """一个记号 → 文字：带项名的按项渲，不带的整条渲。

    单项引用渲的是**值**不是名，故用不上展示名——展示名只在整条并列多项时才需要。
    """
    if item_name is None:
        return format_anchor_value(anchor, item_labels)
    return format_anchor_item(anchor, item_name)


def replace_placeholders(
    text: str,
    anchors_by_id: dict[str, ReportAnchor],
    item_labels: ItemLabels | None = None,
) -> str:
    """正文记号 → 落点值文字。失败明细收齐后一次性报出（fail loud，不是碰到第一个就停）。"""
    details: list[str] = []
    reported: set[str] = set()

    def _sub(match: re.Match[str]) -> str:
        token, lkp_id, item_name = match.group(0), match.group(1), match.group(2)
        anchor = anchors_by_id.get(lkp_id)
        try:
            if anchor is None:
                raise RenderError([f"占位符 {token} 在数据包 anchors 中无落点"])
            return render_reference(anchor, item_name, item_labels)
        except RenderError as exc:
            if token not in reported:
                reported.add(token)
                details.extend(exc.details)
            return ""

    out = PLACEHOLDER_RE.sub(_sub, text)
    if details:
        raise RenderError(details)
    return out
