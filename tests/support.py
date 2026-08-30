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
            # range（一个匿名项，值是区间）+ 经验条目（source=None：标注呈现"经验判断"口径，
            # 禁编造来源）
            "lkpId": "lkp-counter-height",
            "name": "橱柜台面高",
            "numberClass": "selection",
            "unit": "mm",
            "valueKind": "range",
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
            # range 的单边界形态（只 min）+ 已校准国标源
            "lkpId": "lkp-passage-main",
            "name": "主通道净宽",
            "numberClass": "analysis",
            "unit": "mm",
            "valueKind": "range",
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
            # single（一个匿名项，值是数）——v2.8 前是 {"v": 2136} 的壳，现直接是标量
            "lkpId": "lkp-wardrobe-rod",
            "name": "衣柜挂杆高",
            "numberClass": "selection",
            "unit": "mm",
            "valueKind": "single",
            "value": 2136,
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
            # 造价形态：range + 复合单位 + 时效（第一个会过期的资产形态）
            "lkpId": "lkp-price-hydro-labor",
            "name": "水电人工费",
            "numberClass": "analysis",
            "unit": "元/㎡",
            "valueKind": "range",
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
        {
            # scenario（多项，各项值是数）：灯光分场景照度——v2.8 前这一形态渲染层直接
            # fail loud，灯光章出不了册。referencePlane 是 v2.8 从 value 里挪出来的字段。
            "lkpId": "lkp-illuminance-living",
            "name": "起居室照度标准值",
            "numberClass": "selection",
            "unit": "lx",
            "valueKind": "scenario",
            "value": {"general": 100, "reading": 300},
            "basisTag": "lighting@v2",
            "source": "GB 50034 表 5.2.1",
            "calibration": "calibrated",
            "degraded": False,
            "provenance": {
                "source": "GB 50034 表 5.2.1",
                "effectiveFrom": "2013-05-01",
                "effectiveTo": None,
                "calibration": "calibrated",
                "annotationRequired": False,
            },
            "presentation": "THESIS_SUPPORT",
            "referencePlane": "0.75m 水平面",
        },
        {
            # dimension（多项，各项值是区间的单边界）：v2.8 前的 {min_w, min_d} 自造缩写
            "lkpId": "lkp-shower-clear",
            "name": "淋浴房内空",
            "numberClass": "selection",
            "unit": "mm",
            "valueKind": "dimension",
            "value": {"depth": {"min": 800}, "width": {"min": 800}},
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
            # tier（多项，各项值是数）：档位闭集 low/medium/high
            "lkpId": "lkp-budget-confidence-width",
            "name": "置信到区间宽度的映射",
            "numberClass": "analysis",
            "unit": None,
            "valueKind": "tier",
            "value": {"high": 0.15, "low": 0.5, "medium": 0.3},
            "basisTag": "budget@v2",
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
            # component（多项，各项值是区间）：造价分项占比。项名只用规范/契约点名的两项，
            # 其余五项待源侧种子改名后进受控词表再补登记（表外项名 fail loud）。
            "lkpId": "lkp-budget-share",
            "name": "分项造价占比带",
            "numberClass": "analysis",
            "unit": None,
            "valueKind": "component",
            "value": {
                "demolition": {"min": 0.03, "max": 0.08},
                "main-material": {"min": 0.2, "max": 0.35},
            },
            "basisTag": "budget@v2",
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
            # comparison（多项，各项值是区间）：档位比较，项名形态 {高档}-vs-{低档}
            "lkpId": "lkp-budget-tier-gap",
            "name": "三档情景价差带",
            "numberClass": "analysis",
            "unit": "倍",
            "valueKind": "comparison",
            "value": {
                "high-vs-medium": {"min": 1.4, "max": 2.2},
                "medium-vs-low": {"min": 1.3, "max": 1.8},
            },
            "basisTag": "budget@v2",
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
                # 单位写在记号后面（用户裁决 2026-08-30 晚）：本层只出数，单位是写手照抄
                # 下发给它的那个字，机检逐字比对这条落点的 unit——单位仍由数据决定
                "thesis": "台面高度按主要下厨者身高定制，建议 {lkp-counter-height} mm",
                "body": "以 1620 mm 身高推算，台面做到 {lkp-counter-height} mm 更省腰；"
                "主通道不低于 {lkp-passage-main} mm 以保证通行。",
                "number_refs": ["lkp-counter-height", "lkp-passage-main"],
                "assertions": [],
            },
            {
                "thesis": "挂杆高度建议 {lkp-wardrobe-rod} mm",
                "body": "常用挂衣区设在 {lkp-wardrobe-rod} mm 附近，取放不需踮脚。",
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
        # 灯光页：整条引用与单项引用同页——单项引用是 v2.8 之前写不出来的写法
        # （模型只能整条引用，"沙发旁读书那块单独加亮"没有合法记号）。
        "page_id": "page-lighting",
        "domain": "lighting",
        "page_type": None,
        "cards": [
            {
                "thesis": "起居室分场景给光：{lkp-illuminance-living}",
                "body": "沙发旁的读书位单独加亮到 {lkp-illuminance-living.reading} lx，"
                "其余区域维持环境照度 {lkp-illuminance-living.general} lx 即可。",
                "number_refs": ["lkp-illuminance-living"],
                "assertions": [],
            }
        ],
        "locked_text_ids": [],
        "provenance_notes": [
            {
                "lkp_id": "lkp-illuminance-living",
                "source": "GB 50034 表 5.2.1",
                "effective_from": "2013-05-01",
                "effective_to": None,
                "calibration": "calibrated",
            }
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


# 落点项名展示名夹具：**照抄 contracts `registries/anchor_items.json` 的 label 列**（开集两类）。
# 它是测试数据不是第二真源——生产路径由 CLI `--anchor-items` 把那份词表原样传进来，本层不存表。
ITEM_LABELS: dict[str, dict[str, str]] = {
    "scenario": {
        "general": "一般活动",
        "reading": "书写阅读",
        "task": "操作台",
        "vanity": "化妆台",
    },
    "component": {
        "main-material": "主材",
        "custom-cabinetry": "定制",
        "demolition": "拆改",
        "plumbing-electrical": "水电",
        "painting": "油漆",
        "masonry-carpentry": "泥木",
        "soft-furnishing": "软装",
        "hang": "悬挂",
        "fold": "叠放",
        "drawer": "抽屉",
        "main": "主色",
        "secondary": "辅色",
        "accent": "点缀色",
    },
}
