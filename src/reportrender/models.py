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
    """落点对象：占位符替换的唯一数据源，一个占位符=整条落点（区间渲染成区间，禁换算）。"""

    lkp_id: str
    name: str
    number_class: str | None = None
    unit: str | None = None
    value: dict[str, Any]
    basis_tag: str
    source: str | None = None
    calibration: str
    degraded: bool
    provenance: AnchorProvenance | None = None
    presentation: Literal["THESIS_SUPPORT", "REFERENCE_ONLY"]


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


def parse_locked_texts(data: Any) -> dict[str, str]:
    """锁定文案数据解析：``{ID: 正文}`` 平面映射。

    缺 ID = 该文案待补录（注册表状态），渲染时**缺席并记录**——缺是少说，编是替企业作
    错误承诺；这里不做任何默认值、拼接或占位正文。
    """
    if not isinstance(data, dict):
        raise ValueError("锁定文案数据须为 {ID: 正文} 映射")
    out: dict[str, str] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"锁定文案条目形态非法：{key!r}")
        out[key] = value
    return out
