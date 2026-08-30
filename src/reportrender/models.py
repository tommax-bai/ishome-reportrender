"""渲染层入参模型（pydantic）：pages（成文线产物）+ 报告数据包（求值线产物）。

两侧序列化形态不同，镜像时各按各的：

- **pages** 来自 reportgen（Python pydantic 默认序列化）——snake_case；
- **数据包** 来自 project-svc（Jackson 序列化，契约 = contracts
  ``rulebook/report_data_package.schema.json``）——camelCase 别名对齐。

解析纪律与成文线同款、**不做宽容解析**：``extra="forbid"`` 使任何未知字段直接解析失败——
输入即匿名（数据包结构性无用户标识）靠的就是这个守卫；``withheldAnchors`` 非空同样整包
失败（v2.4 作废字段恒空，非空说明生产方还停在隐藏档，那时失败比宽容更安全）。

渲染层只消费数据包的一小部分（落点、求值基准日、锁定清单）；persona/判据/禁词等成文线
载荷在此声明为松散类型——顶层字段全集仍然封闭（匿名守卫在顶层），载荷内部不是渲染层的
消费面，镜像其结构只会造出第三份会漂移的副本。
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

# ---------------------------------------------------------------------------
# 数据包侧（camelCase）
# ---------------------------------------------------------------------------


class _PackageModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class AnchorProvenance(_PackageModel):
    """落点依据（规则 4.10c 标注必挂）：渲染层出"本页依据"块的数据源。

    ``source is None`` **是事实不是缺失**——经验条目（规则 4.10 无外部依据、靠行业判断），
    渲染层据此呈现"经验判断"口径，**禁编造一个来源**。
    """

    source: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    calibration: str
    annotation_required: bool


class ReportAnchor(_PackageModel):
    """落点对象：占位符替换的唯一数据源。

    **两层模型**（规则 1.9，v2.8）：一条落点 = 若干「项」，一项的值 = 一个数或一个区间。
    ``value_kind`` 判定 ``value`` 的形态与可否单项引用，**消费侧按它分支、不靠推断键名**；
    七值闭集照契约镜像成 ``Literal``，第八个值即解析失败（同 ``presentation``）。

    **元信息不进 value**（规则 1.9 二）：单位在 ``unit``、参考平面在 ``reference_plane``——
    与项同层则 ``{lkp-x.unit}``（引用出一个单位字符串）就是语法上合法的写法，约定管不住。
    """

    lkp_id: str
    name: str
    number_class: str | None = None
    unit: str | None = None
    value_kind: Literal[
        "single", "range", "scenario", "tier", "dimension", "component", "comparison"
    ]
    # single = 标量；range = {min,max}；其余五类 = 项名 → 标量 | {min,max}。
    value: int | float | dict[str, Any]
    basis_tag: str
    source: str | None = None
    calibration: str
    degraded: bool
    provenance: AnchorProvenance | None = None
    presentation: Literal["THESIS_SUPPORT", "REFERENCE_ONLY"]
    # 参考平面（国标术语，如"0.75m 水平面"）：v2.8 从 value 里挪出来的独立字段。
    # **本轮解析但不上纸**——形态与挂载位都未定，理由与触发条件见 anchor_text 模块 docstring。
    reference_plane: str | None = None


class ReleaseRef(_PackageModel):
    domain: str
    release_tag: str


class RenderPackage(_PackageModel):
    """报告数据包（渲染层视角）。

    顶层字段全集 = contracts schema 全集（``extra="forbid"`` 匿名守卫要求声明齐）；
    渲染层实际只读 ``anchors``（占位符替换与标注名称 join）与 ``evaluated_on``（封面基准日）。
    """

    entitlement: Literal["FREE", "PAID"]
    evaluated_on: str | None = None
    domains: list[str]
    releases: list[ReleaseRef]
    anchors: list[ReportAnchor]
    withheld_anchors: list[Any] = []
    gaps: list[Any] = []
    personas_by_domain: dict[str, Any] = {}
    checks_by_domain: dict[str, Any] = {}
    banned_terms_by_domain: dict[str, Any] = {}
    locked_texts_by_domain: dict[str, list[str]] = {}
    anonymous_profile: dict[str, Any] = {}
    triggered_rules_by_domain: dict[str, Any] = {}
    """求值线判定的触发规则条目（获客线「户型特征进报告」，contracts 2026-08-30 新增，非必填）。

    **本层声明它但不渲它**：它是给成文线定"讲什么"的输入，纸面上没有它的位置——真要上纸，
    上的是成文线据它写出的那句话，不是条目本身。声明的理由是 ``extra="forbid"``：顶层字段
    全集必须齐，少声明一个，整包当场解析失败（本条正是这么被真跑逮到的）。

    后续路径：若将来它要在纸面上单独成节（如"这套户型触发了哪些做法"），触发条件＝成文线在
    pages 上给出承载位；在那之前本层只认不渲。"""

    @field_validator("withheld_anchors")
    @classmethod
    def _withheld_must_be_empty(cls, v: list[Any]) -> list[Any]:
        # v2.4 作废字段恒空：非空 = 生产方还在隐藏落点（违约），整包失败是故意的严。
        if v:
            raise ValueError("withheldAnchors 非空：生产方仍在发隐藏档（v2.4 已作废），拒绝解析")
        return v

    def anchors_by_id(self) -> dict[str, ReportAnchor]:
        return {a.lkp_id: a for a in self.anchors}


# ---------------------------------------------------------------------------
# pages 侧（snake_case，reportgen Page 契约镜像）
# ---------------------------------------------------------------------------


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")

    thesis: str
    body: str
    number_refs: list[str] = []
    assertions: list[str] = []


class ProvenanceNote(BaseModel):
    """页上的依据标注（结构化数据，正文由渲染层按字段出——gen-locked 零生成）。

    只有 ``lkp_id`` 没有名称：**展示名必须从数据包 anchors join**，直接打印 id 即违规
    （客户语域禁内部编号）。
    """

    model_config = ConfigDict(extra="forbid")

    lkp_id: str
    source: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    calibration: str


class Page(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_id: str
    domain: str
    page_type: str | None = None
    cards: list[Card]
    locked_text_ids: list[str] = []
    provenance_notes: list[ProvenanceNote] = []


def parse_pages(data: Any) -> list[Page]:
    """pages 输入解析：裸数组，或带 ``pages`` 键的对象（装配 activity 结果原样落盘的形态）。"""
    if isinstance(data, dict) and "pages" in data:
        data = data["pages"]
    if not isinstance(data, list):
        raise ValueError("pages 输入须为 Page 数组，或含 pages 键的对象")
    return [Page.model_validate(item) for item in data]


def parse_anchor_items(data: Any) -> dict[str, dict[str, str]]:
    """落点项名展示名解析（contracts ``registries/anchor_items.json`` 的形态）。

    返回 ``{valueKind: {项名: 展示名}}``。**开集两类（scenario/component）的展示名是词表的一列，
    本层不另存一份**——存两份就是同一条词表两处各写一遍，源侧长出新词而这边忘了改，整册当场渲不出来
    （同"投影规则两处各写一遍"的既有坑）。闭集两类（tier/dimension）不走本表：它们的取值由规范定死，
    新增取值本就要改规范，故展示名留在本层代码里。

    缺省 = 空表：开集项名一个都渲不出，整条引用即 fail loud 并报明细。
    **缺是渲不出，不是猜一个中文名**。
    """
    if not isinstance(data, dict):
        raise ValueError("落点项名词表须为对象")
    items = data.get("items", data)
    if not isinstance(items, dict):
        raise ValueError("落点项名词表缺 items")
    out: dict[str, dict[str, str]] = {}
    for kind, entries in items.items():
        if kind.startswith("$") or not isinstance(entries, dict):
            continue
        table: dict[str, str] = {}
        for name, body in entries.items():
            label = body.get("label") if isinstance(body, dict) else body
            if isinstance(label, str) and label:
                table[name] = label
        out[kind] = table
    return out


def parse_locked_texts(data: Any) -> dict[str, str]:
    """锁定文案数据解析。

    认 contracts ``registries/locked_texts.json`` 的形态（``{"texts": {ID: 正文|null}}``），
    也认裸 ``{ID: 正文}`` 映射。``null`` 与缺 ID 同义 = 正文待补录，渲染时**缺席并记录**——
    缺是少说，编是替企业作错误承诺；这里不做任何默认值、拼接或占位正文。
    """
    if isinstance(data, dict) and isinstance(data.get("texts"), dict):
        data = data["texts"]
    if not isinstance(data, dict):
        raise ValueError("锁定文案数据须为 {ID: 正文} 映射或含 texts 键的对象")
    out: dict[str, str] = {}
    for key, value in data.items():
        if key == "$comment" or value is None:
            continue
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"锁定文案条目形态非法：{key!r}")
        out[key] = value
    return out
