"""锁定文案数据解析：认 contracts 投影形态，null=待补录不入映射。"""

from __future__ import annotations

import pytest

from reportrender.models import parse_locked_texts


def test_contracts_projection_form() -> None:
    data = {
        "$comment": "投影说明",
        "texts": {"GUIDE_SITE_CHECK": "请在水电交底当天……", "DISCLAIM_PRICE": None},
    }
    out = parse_locked_texts(data)
    assert out == {"GUIDE_SITE_CHECK": "请在水电交底当天……"}  # null 不入映射=渲染缺席


def test_flat_map_form_still_accepted() -> None:
    assert parse_locked_texts({"A_B": "正文"}) == {"A_B": "正文"}


def test_malformed_entry_rejected() -> None:
    with pytest.raises(ValueError, match="形态非法"):
        parse_locked_texts({"texts": {"A_B": 42}})
