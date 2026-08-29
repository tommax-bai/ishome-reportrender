# ishome-reportrender

报告渲染层：把成文线产出的 **pages** 与求值线产出的**报告数据包**渲染成一册**自包含 HTML**
（可打印 A4；PDF 走浏览器打印）。

**形态（裁决 2026-08-29）**：不成服务，以工具（纯库 + CLI）形式存在，后续报告产出上线
（"报告一键触发"接进编排）时建立服务——届时包一层 Temporal worker（activity
`report-book-render`，队列 `reportrender-activities`，注册走 contracts PR）。

## 用法

```bash
uv run reportrender --pages pages.json --package package.json \
  --locked-texts locked_texts.json -o book.html
```

- `pages.json`：装配产物（`Page` 数组，或含 `pages` 键的对象）；
- `package.json`：报告数据包（contracts `rulebook/report_data_package.schema.json`）；
- `--locked-texts`：锁定文案数据 `{ID: 正文}`，缺省=全部按待补录缺席（缺是少说，禁编造）。

## 红线（违反即返工，全文见中控仓《交接文档-报告渲染启动.md》§三）

1. **零 LLM**：整层无一次模型调用——gen-locked 的执行者，不是生成者。
2. **锁定文案禁编造、禁拼接**：正文只按 ID 逐字出，缺正文=缺席并记录。
3. **数字原样输出，禁换算折算**：一个占位符=整条落点，区间渲染成区间。
4. **fail loud**：占位符无落点、值形态不认识 → 整册失败并报明细，不空替不静默。
5. **不重判**：pages 已过册级校验，本层只执行。
6. **`lkp-` 等内部编号禁入输出**：标注展示用落点名称（从数据包 join）。
7. **匿名**：输入即匿名，不添加任何来源之外的信息。

## 质量门

本地 pre-push（新 clone 后执行一次 `git config core.hooksPath .githooks`）：
ruff / ruff format / import-linter / mypy strict / pytest。
