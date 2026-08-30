# ishome-reportrender

报告渲染层：把成文线产出的 **pages** 与求值线产出的**报告数据包**渲染成一册**自包含 HTML**
（可打印 A4；PDF 走浏览器打印）。

**形态（裁决 2026-08-29 → 2026-08-30 晚兑现后半段）**：原口径是"不成服务，以工具形式存在，
**后续报告产出上线时建立服务**"。**触发条件已到**（用户 2026-08-30 晚定"尽快让真人用上"，
报告要交到业主手上），服务已建立：Temporal worker 监听 `reportrender-activities`，
承接 activity `report-book-render`（contracts 注册表 #14）。

**CLI 不废**：它是本地迭代的入口——改样式、看一册长什么样走它，不必起 Temporal，也不碰对象存储。
两条路的分界由 import-linter 锁死（`cli` 看不见 `activities`）：从它能看见起，
"本地改样式不需要凭证"就只是一句承诺而不是结构。

## 用法

```bash
uv run reportrender --pages pages.json --package package.json \
  --locked-texts locked_texts.json --anchor-items anchor_items.json -o book.html
```

- `pages.json`：装配产物（`Page` 数组，或含 `pages` 键的对象）；
- `package.json`：报告数据包（contracts `rulebook/report_data_package.schema.json`）；
- `--locked-texts`：锁定文案数据 `{ID: 正文}`，缺省=全部按待补录缺席（缺是少说，禁编造）。
- `--anchor-items`：落点项名受控词表（contracts `registries/anchor_items.json`）——开集两类
  （分场景/分项）并列多项时的**展示名**。缺省=空表，这两类的整条引用即 fail loud。
  **展示名不在本层存**：它是词表的一列，本层再存一份就是同一条词表两处各写一遍，源侧长出新词而
  这边忘了改、整册当场渲不出来。闭集两类（档位 低/中/高、维度 宽/深/高）由规范定死，留在本层代码里。

## 出册服务（`reportrender-worker`）

```bash
set -a; source ~/.ishome/oss-local.env; set +a          # 私有桶凭证，不入库
export ISHOME_CONTRACTS_REGISTRIES_DIR=~/codes/ishome-contracts/registries
uv run reportrender-worker                              # 监听 reportrender-activities
```

- **册写进私有对象存储**（阿里云 OSS 私有桶，用户裁决 2026-08-30 晚），键由 `report_id`
  确定性推得：`reports/{report_id}/book.html`（唯一真源 contracts `registries/object_keys.md`）。
  因此"这份报告出没出册"**问存储即知，不另立台账**——台账会与真相漂移，派生不会；
- **只写不签**。签名是"给谁看、看多久"的事，属业务侧（project-svc `GET /api/v1/reports/{id}/link`）
  ——生成侧不知用户是谁；
- **两份词表从 contracts 注册表目录读，本仓不留副本**，进程起来时装好并当场校验：
  缺配置要在 worker 起不来的时候就知道，不是等第一份报告渲完才发现册存不进去；
- **写不进去就不是 ok**：册渲得再好、落不了地也按失败回报——回一个指向空气的键，
  业务侧会去签一条打不开的链接发给业主，那是这条线最贵的失效形态。

## 红线（违反即返工，全文见中控仓《交接文档-报告渲染启动.md》§三）

1. **零 LLM**：整层无一次模型调用——gen-locked 的执行者，不是生成者。
2. **锁定文案禁编造、禁拼接**：正文只按 ID 逐字出，缺正文=缺席并记录。
3. **数字原样输出，禁换算折算**：区间渲染成区间（不取中值不挑一头），mm 不折 m、0.03 不变 3%。
4. **fail loud**：占位符无落点、按项引用了只有匿名项的落点、项名不存在、值形态不认识 →
   整册失败并报明细，不空替不静默。
5. **不重判**：pages 已过册级校验，本层只执行。
6. **`lkp-` 等内部编号禁入输出**：标注展示用落点名称（从数据包 join）；**项名同理**——
   渲染出去的是值不是名，多项并列时的中文展示名逐项登记，表外项名 fail loud。
7. **匿名**：输入即匿名，不添加任何来源之外的信息。

## 落点引用形态（规范规则 1.9，v2.8）

两层模型：**一条落点 = 若干「项」；一项的值 = 一个数，或一个区间**。正文两种写法——
整条 `{lkp-x}`、单项 `{lkp-x.项名}`。`valueKind` 七值闭集（`single`/`range`/`scenario`/
`tier`/`dimension`/`component`/`comparison`）随落点下发，可引用性与呈现形态**都按它分支、
不推断键名**：`single`/`range` 只有一个匿名项（按项引用即失败），其余五类可单项引用。
七类各自的文字形态见 `anchor_text` 模块 docstring 的登记表。

参考平面（`referencePlane`）本轮**解析但不上纸**（形态与挂载位待定，理由与触发条件同上）。

## 质量门

本地 pre-push（新 clone 后执行一次 `git config core.hooksPath .githooks`）：
ruff / ruff format / import-linter / mypy strict / pytest。
