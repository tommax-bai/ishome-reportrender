"""测试夹具：最小合成数据包 + pages（形态对齐 reportgen 夹具与 contracts schema）。

锁定文案正文夹具只收注册表里"正文已登记"的条目**逐字副本**（来源 contracts
``registries/locked_texts.md``）——测试专用，不是第二真源；生产数据待锁定文案数据化
落 contracts 后由一致性校验钉住。
"""

from __future__ import annotations

from typing import Any

PACKAGE_JSON: dict[str, Any] = {
    "entitlement": "PAID",
    "evaluatedOn": "2026-08-29",
    "domains": ["ergonomics", "lighting"],
    "releases": [
        {"domain": "ergonomics", "releaseTag": "ergonomics@v1"},
        {"domain": "lighting", "releaseTag": "lighting@v2"},
    ],
    "anchors": [
        {
            # 区间形态 + 经验条目（source=None：标注呈现"经验判断"口径，禁编造来源）
            "lkpId": "lkp-counter-height",
            "name": "橱柜台面高",
            "numberClass": "selection",
            "unit": "mm",
            "value": {"min": 900, "max": 950},
            "basisTag": "ergonomics@v1",
            "source": None,
            "calibration": "draft",
            "degraded": True,
            "provenance": {
                "source": None,
                "effectiveFrom": None,
                "effectiveTo": None,
                "calibration": "draft",
                "annotationRequired": True,
            },
            "presentation": "REFERENCE_ONLY",
        },
        {
            # 单边界形态（只 min）+ 已校准国标源
            "lkpId": "lkp-passage-main",
            "name": "主通道净宽",
            "numberClass": "analysis",
            "unit": "mm",
            "value": {"min": 900},
            "basisTag": "ergonomics@v1",
            "source": "GB 50352 条文",
            "calibration": "calibrated",
            "degraded": False,
            "provenance": {
                "source": "GB 50352 条文",
                "effectiveFrom": "2019-09-01",
                "effectiveTo": None,
                "calibration": "calibrated",
                "annotationRequired": False,
            },
            "presentation": "THESIS_SUPPORT",
        },
        {
            # 点值形态
            "lkpId": "lkp-wardrobe-rod",
            "name": "衣柜挂杆高",
            "numberClass": "selection",
            "unit": "mm",
            "value": {"v": 2136},
            "basisTag": "ergonomics@v1",
            "source": "行业通行",
            "calibration": "draft",
            "degraded": True,
            "provenance": {
                "source": "行业通行",
                "effectiveFrom": None,
                "effectiveTo": None,
                "calibration": "draft",
                "annotationRequired": True,
            },
            "presentation": "REFERENCE_ONLY",
        },
        {
            # 造价形态：区间 + 复合单位 + 时效（第一个会过期的资产形态）
            "lkpId": "lkp-price-hydro-labor",
            "name": "水电人工费",
            "numberClass": "analysis",
            "unit": "元/㎡",
            "value": {"min": 60, "max": 68},
            "basisTag": "budget@v2",
            "source": "市场行情采集",
            "calibration": "calibrated",
            "degraded": False,
            "provenance": {
                "source": "市场行情采集",
                "effectiveFrom": "2026-08-27",
                "effectiveTo": "2026-11-27",
                "calibration": "calibrated",
                "annotationRequired": False,
            },
            "presentation": "THESIS_SUPPORT",
        },
    ],
    "withheldAnchors": [],
    "gaps": [],
    "personasByDomain": {},
    "checksByDomain": {},
    "bannedTermsByDomain": {},
    "lockedTextsByDomain": {"ergonomics": ["GUIDE_SITE_CHECK"]},
    "anonymousProfile": {"chiefHeightMm": 1620, "cityTier": "一线"},
}

PAGES_JSON: list[dict[str, Any]] = [
    {
        "page_id": "page-ergonomics",
        "domain": "ergonomics",
        "page_type": None,
        "cards": [
            {
                "thesis": "台面高度按主要下厨者身高定制，建议 {lkp-counter-height}",
                "body": "以 1620 mm 身高推算，台面做到 {lkp-counter-height} 更省腰；"
                "主通道保持 {lkp-passage-main} 以保证通行。",
                "number_refs": ["lkp-counter-height", "lkp-passage-main"],
                "assertions": [],
            },
            {
                "thesis": "挂杆高度建议 {lkp-wardrobe-rod}",
                "body": "常用挂衣区设在 {lkp-wardrobe-rod} 附近，取放不需踮脚。",
                "number_refs": ["lkp-wardrobe-rod"],
                "assertions": [],
            },
        ],
        "locked_text_ids": ["GUIDE_SITE_CHECK", "DISCLAIM_PRICE"],
        "provenance_notes": [
            {
                "lkp_id": "lkp-counter-height",
                "source": None,
                "effective_from": None,
                "effective_to": None,
                "calibration": "draft",
            },
            {
                "lkp_id": "lkp-wardrobe-rod",
                "source": "行业通行",
                "effective_from": None,
                "effective_to": None,
                "calibration": "draft",
            },
        ],
    },
    {
        "page_id": "page-budget",
        "domain": "budget",
        "page_type": None,
        "cards": [
            {
                "thesis": "水电改造按 {lkp-price-hydro-labor} 预留人工费",
                "body": "一线档行情为 {lkp-price-hydro-labor}，按实测点位数结算。",
                "number_refs": ["lkp-price-hydro-labor"],
                "assertions": [],
            }
        ],
        "locked_text_ids": [],
        "provenance_notes": [
            {
                "lkp_id": "lkp-price-hydro-labor",
                "source": "市场行情采集",
                "effective_from": "2026-08-27",
                "effective_to": "2026-11-27",
                "calibration": "calibrated",
            }
        ],
    },
]

# 注册表"正文已登记"条目的逐字副本（见模块 docstring）；DISCLAIM_PRICE 故意不在——
# 注册表状态=待补录，夹具据此测"缺席不编造"路径。
LOCKED_TEXTS_JSON: dict[str, str] = {
    "GUIDE_SITE_CHECK": "请在水电交底当天，携带本清单与施工方逐项现场确认并勾选。",
    "DISCLAIM_P1": "本图为点位逻辑示意，标注为相对位置，不含施工坐标。"
    "具体尺寸与定位以现场交底、现场复核为准。本图纸为参考级设计产物，不构成施工指令。",
}
