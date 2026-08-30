# ishome-reportrender

报告渲染层：把成文线产出的 **pages** 与求值线产出的**报告数据包**渲染成一册**自包含 HTML**
（可打印 A4；PDF 走浏览器打印）。

**形态（裁决 2026-08-29）**：不成服务，以工具（纯库 + CLI）形式存在，后续报告产出上线
（"报告一键触发"接进编排）时建立服务——届时包一层 Temporal worker（activity
`report-book-render`，队列 `reportrender-activities`，注册走 contracts PR）。

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
