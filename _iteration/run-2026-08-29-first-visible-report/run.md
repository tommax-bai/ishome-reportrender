# 真跑 · 第一份可见报告 · 2026-08-29 晚

> 目的：渲染专项验收——第一份人能看到的报告。产物 `book.html`（人体工学一章 23 卡 23 标注）。
> 纪律：本文所有违规句与计数逐字取自真跑输出。

## 一、输入

- `package.json`：主线 17:12 一次性只读导包（PAID 三域 44 落点，releases budget@v7 /
  ergonomics@v6 / lighting@v7），取自 /tmp 快照。
- `unit-ergonomics-mainline-1744.json`：主线 17:44 过检单元（verdict=ok，23 卡，重写 1 轮，
  即《run-2026-08-29-judge-batching.md》的"稿二"）——交接文档指名的验收输入。

## 二、本 session 三域补跑：全部 failed（unit-*.json 留档）

同码（reportgen `15c87d3` 干净克隆）同参（qwen-plus，temperature=0，max_rewrites=2）重跑三域，
全部两轮未收敛：budget=裸 lkp- 标识入正文 + 禁词「依据」+ cr-methodology-language；
ergonomics=拆区间两端自造占位符（lkp-bed-height-min/max 等）；lighting=同病 26 条。
均为已登记的写手病（主线正在做叙事推导拆两步治它）。**同参不同果**：主线 17:44 同域一次
重写即 ok——网关 temperature=0 输出仍不严格确定，写手收敛是概率事件不是保证。
判官台账（judge-ledger.jsonl）本轮空：规则层没放行过，判官一次都没到。

## 三、装配与册检（如实）

ok 单元只有人体工学一份 → 装配 ok（1 页）；**册检 failed**：`gate-domain-page-missing`
budget/lighting 无页。**本册是三域包下的部分册**，册检打回是正确行为；首份可见报告按交接
口径渲过检的那部分，此失败判定随档如实保留，不视为放行。

## 四、渲染两次 fail loud，各立一案

1. **`lkp-shower-clear` 值形态 `{min_w,min_d}`**：种子定义=淋浴房内空宽/深两轴下限（backend
   既有称呼"前缀边界"）。**已登记为渲染第四形态**（逐轴出：`宽不低于 800 mm、深不低于 800 mm`），
   轴键闭集只收真源出现过的（min_w/min_d），表外键照旧 fail loud。
2. **`lkp-chair-height` 的 provenance.source 含内部落点编号**（"同 lkp-desk-height：GB/T
   3326-2016 标准号已定位，数值表未取到。旧版单源旁证：……单源不足以采"）——出口自检拒绝出册。
   定性：**source 字段的现状是获取回路的审计叙事，不是客户引文**（内部编号+方法论语言+旁证推理，
   全字段如此，非一条脏数据）。渲染层禁改写、禁静默逐条取舍 → **来源列整列待裁**：页脚暂只渲
   名称/取数时间/校准状态三项纯结构化事实；"经验判断、无外部标准背书"话术原挂来源列，一并待裁。
   **建议裁决方向**：获取侧拆 `citation`（客户可见引文）与 `audit_note`（审计叙事）两字段改源。

## 五、成品抽查新立一案：单边界措辞叠字

`床侧留出不少于{lkp-bed-side}的空间` + 渲染 `{min:750}` → "不低于 750 mm" =
**"不少于不低于 750 mm"**。写手文句自带边界词（本册 7 处），渲染层单边界措辞与之叠加。
表示问题按红线上报待裁，不猜。候选：①单边界渲裸值（边界语义归写手文句——风险=文句不带边界词时
裸值被读成点值）；②写手侧禁在占位符前写边界词（判据可机检）；③维持现状容忍叠字。
区间与点值形态无此问题。

## 六、产物清单

| 文件 | 内容 |
|---|---|
| `book.html` | **第一份可见报告**（封面/目录/人体工学章 23 卡/页脚 23 条标注） |
| `pages.json` / `book-check.json` | 装配产物与册检结果（failed 如实留档） |
| `unit-{budget,ergonomics,lighting}.json` | 本 session 三域 failed 留档 |
| `unit-ergonomics-mainline-1744.json` | 主线过检单元（成书输入） |
| `judge-ledger.jsonl` | 空（本轮判官未到场） |

锁定文案：包内锁定清单为空（一次性导包未按产物传入）+ 七条正文待补录 → 本册无文案，
缺席合规。样式=最简可读基线，美化等页型库（pt-）落地（交接文档坑 8）。
