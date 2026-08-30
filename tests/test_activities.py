"""出册 activity：正路径、四条失败路径，以及"写不进存储不许当成功"。

**存储用桩件不用真桶**：这一层要验的是"册渲出来之后往哪走、走不通怎么办"，
真桶验的是凭证与网络对不对——那件事由真跑存档留档，不是单测的题目。
"""

from __future__ import annotations

from typing import Any

import pytest

from reportrender.activities import ACTIVITY_REPORT_BOOK_RENDER, ReportBookRenderer
from reportrender.book_store import REPORT_BOOK_KEY_TEMPLATE, BookStoreError, book_key_of
from tests.support import ITEM_LABELS, LOCKED_TEXTS_JSON, PACKAGE_JSON, PAGES_JSON

_REPORT_ID = "01M18E1YGKVQZGCCNB0PCY4K7B"


class _StubBookStore:
    """桩件私有桶：记下写了什么，或按需当场失败。"""

    def __init__(self, *, fail_with: str | None = None) -> None:
        self.written: dict[str, str] = {}
        self._fail_with = fail_with

    @property
    def bucket_name(self) -> str:
        return "ishome-test"

    def put_book(self, report_id: str, html: str) -> str:
        if self._fail_with is not None:
            raise BookStoreError([self._fail_with])
        key = book_key_of(report_id)
        self.written[key] = html
        return key


def _renderer(store: Any) -> ReportBookRenderer:
    return ReportBookRenderer(store, dict(LOCKED_TEXTS_JSON), ITEM_LABELS)


def _request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "report_id": _REPORT_ID,
        "pages": PAGES_JSON,
        "package": PACKAGE_JSON,
    }
    request.update(overrides)
    return request


async def test_renders_and_writes_the_book() -> None:
    store = _StubBookStore()
    result = await _renderer(store).render_report_book(_request())

    assert result["verdict"] == "ok"
    assert result["book_key"] == f"reports/{_REPORT_ID}/book.html"
    assert result["page_count"] == len(PAGES_JSON)
    assert result["card_count"] > 0
    # 册确实落进了存储，而且落的就是回报的那个键——不是回一个指向空气的键。
    assert result["book_key"] in store.written
    assert store.written[result["book_key"]].startswith("<!doctype html>")


async def test_store_failure_is_not_reported_as_success() -> None:
    """写不进去就是这份报告没出来。册渲得再好，落不了地也不是 ok。"""
    store = _StubBookStore(fail_with="桶不存在")
    result = await _renderer(store).render_report_book(_request())

    assert result["verdict"] == "failed"
    assert [v["check"] for v in result["violations"]] == ["book-store-failed"]
    assert "桶不存在" in result["violations"][0]["detail"]


@pytest.mark.parametrize(
    ("overrides", "expected_check"),
    [
        ({"report_id": ""}, "gate-missing-report-id"),
        ({"pages": []}, "gate-empty-pages"),
        ({"package": {"entitlement": "什么鬼"}}, "gate-bad-input"),
    ],
)
async def test_bad_input_fails_loud(overrides: dict[str, Any], expected_check: str) -> None:
    """入参不成立时说清是哪一条不成立，不出半册也不出空册。"""
    store = _StubBookStore()
    result = await _renderer(store).render_report_book(_request(**overrides))

    assert result["verdict"] == "failed"
    assert [v["check"] for v in result["violations"]] == [expected_check]
    assert store.written == {}


def test_activity_registration_name_matches_contracts() -> None:
    """注册名逐字对齐 contracts `activities/registry.md` #14（只增不改）。"""
    from temporalio import activity

    assert ACTIVITY_REPORT_BOOK_RENDER == "report-book-render"
    defn = activity._Definition.from_callable(ReportBookRenderer.render_report_book)  # noqa: SLF001
    assert defn is not None
    assert defn.name == ACTIVITY_REPORT_BOOK_RENDER
    # 函数名 = 同词 snake_case 动词前置（规范 §2.4）
    assert ReportBookRenderer.render_report_book.__name__ == "render_report_book"


def test_book_key_is_derived_not_recorded() -> None:
    """对象键由 report_id 确定性推得——签名的那一侧不必查任何台账就能算出同一个键。

    键模板的唯一真源在 contracts `registries/object_keys.md`，本行是逐字副本；
    两处对不上就是写的一侧与签的一侧接不上头（见 `book_store` 模块文档）。
    """
    assert REPORT_BOOK_KEY_TEMPLATE == "reports/{report_id}/book.html"
    assert book_key_of(_REPORT_ID) == f"reports/{_REPORT_ID}/book.html"
    # 同一份报告重跑落同一个对象，天然幂等。
    assert book_key_of(_REPORT_ID) == book_key_of(_REPORT_ID)


def test_report_id_that_cannot_be_a_key_fails_loud() -> None:
    """report_id 带斜杠会把对象写到别处去——响亮失败，不悄悄改写它。"""
    with pytest.raises(BookStoreError):
        book_key_of("../../etc/passwd")
