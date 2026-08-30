"""Temporal activity：`report-book-render`——册检通过后出册并写进私有对象存储。

注册名唯一真源：ishome-contracts `activities/registry.md` #14，**只增不改**；
命名规则（规范 §2.4）：注册名 kebab-case 显式声明，函数名同词 snake_case 动词前置。

**渲染层至此成服务**。裁决 2026-08-29 的原话是"不成服务，以工具形式存在，**后续报告产出
上线时，建立服务**"——报告要交到真人手上，触发条件即此（用户 2026-08-30 晚定"尽快让真人用上"）。
CLI 不废：它是本地迭代的入口，改样式、看一册长什么样都走它，不必起 Temporal。

纪律（与本层既有红线一致）：
- **确定性、零 LLM**：本 activity 不调任何模型，只是把已经定稿的内容排成一册；
- **任一页渲不出即整册失败**，不出"其余页"（同成文线"任一域失败整册失败"）；
- **锁定文案缺席是少说不是失败**：缺了逐条回报，不编造正文；
- 写不进存储即失败——册没落地就是这份报告没出来，不许当成功回报。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from temporalio import activity

from reportrender.anchor_text import ItemLabels, RenderError
from reportrender.book_store import BookStoreError, OssBookStore
from reportrender.models import RenderPackage, parse_pages
from reportrender.render import render_book

ACTIVITY_REPORT_BOOK_RENDER = "report-book-render"
"""contracts 注册名（#14）。字符串在此声明一次，worker 与守门测试都引它。"""


class ReportBookRenderer:
    """出册 activity 的实现件，依赖由组合根（worker）注入。

    做成类而不是自由函数，是因为它要用两样**进程级**的东西：私有桶的连接、以及 contracts
    注册表里的锁定文案与落点项名词表。两样都该在**起进程时**装好并当场校验——
    缺配置要在 worker 起不来的时候就知道，不是等第一份报告渲完才发现册存不进去。
    """

    def __init__(
        self,
        store: OssBookStore,
        locked_texts: dict[str, str],
        item_labels: ItemLabels,
    ) -> None:
        self._store = store
        self._locked_texts = locked_texts
        self._item_labels = item_labels

    @activity.defn(name=ACTIVITY_REPORT_BOOK_RENDER)
    async def render_report_book(self, request: dict[str, Any]) -> dict[str, Any]:
        """pages + 报告数据包 → 单册自包含 HTML → 写私有桶，返回对象键。

        入参是**不透明字典**而不是本仓模型：派发方（genpipe 编排）不 import 本仓存根签名，
        两边只靠 contracts 注册名接头（同成文线三个 activity 的口径）。
        """
        report_id = str(request.get("report_id") or "")
        if not report_id:
            return _failed("gate-missing-report-id", "没有 report_id：册的对象键由它推得，无从落地")
        try:
            pages = parse_pages(request.get("pages"))
            package = RenderPackage.model_validate(request.get("package"))
        except (ValueError, TypeError) as e:
            return _failed("gate-bad-input", f"入参解析失败：{e}")
        if not pages:
            return _failed("gate-empty-pages", "一页都没有：空册不是册")

        try:
            result = render_book(pages, package, self._locked_texts, self._item_labels)
        except RenderError as e:
            # 渲不出即整册失败，逐条回报违规——不空替、不静默跳过（本层红线）。
            return {
                "verdict": "failed",
                "violations": [{"check": "render-failed", "detail": line} for line in e.details],
            }

        try:
            book_key = self._store.put_book(report_id, result.html)
        except BookStoreError as e:
            return {
                "verdict": "failed",
                "violations": [
                    {"check": "book-store-failed", "detail": line} for line in e.details
                ],
            }

        return {
            "verdict": "ok",
            "book_key": book_key,
            "bucket": self._store.bucket_name,
            "page_count": result.page_count,
            "card_count": result.card_count,
            # 缺席是少说不是失败，但缺了多少必须让人看见（同 CLI 的口径）。
            "missing_locked_texts": [
                {"page_id": page_id, "text_id": text_id}
                for page_id, text_id in result.missing_locked_texts
            ],
            "warnings": list(result.warnings),
        }


def _failed(check: str, detail: str) -> dict[str, Any]:
    return {"verdict": "failed", "violations": [{"check": check, "detail": detail}]}


def activity_registry(renderer: ReportBookRenderer) -> dict[str, Callable[..., Any]]:
    """本仓承接的 activity 全集（队列 `reportrender-activities`）。"""
    return {ACTIVITY_REPORT_BOOK_RENDER: renderer.render_report_book}
