"""册页渲染：pages + 数据包 → 单册自包含 HTML（可打印 A4）。

本层是 gen-locked 的执行者：卡片正文只做占位符替换（:mod:`reportrender.anchor_text`）、
锁定文案按 ID 逐字取正文、依据标注按结构化字段出文字——**没有一处内容是这里发明的**，
渲染层不得添加任何来源之外的信息（输入即匿名，输出同样匿名）。

样式纪律：验收是"能读"不是"好看"——先让卡片、标注、文案全部如实出现在纸面上，
美化等页型库（pt-）落地再说。
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field

from reportrender.anchor_text import RenderError, replace_placeholders
from reportrender.models import Page, ProvenanceNote, RenderPackage, ReportAnchor

# 章题展示名：dom- 域名是内部标识，客户语域用中文章题。未登记的域用原名渲出并记警告
# （不 fail：新域先能读，展示名补表跟上）。
DOMAIN_TITLES = {
    "ergonomics": "人体工学",
    "lighting": "灯光",
    "budget": "造价",
    "hydro": "水电",
    "acceptance": "验收",
    "quotation": "报价",
}

# 校准状态展示名：契约闭集，未知值 fail loud（渲染层不发明第四种状态的说法）。
_CALIBRATION_LABELS = {
    "calibrated": "已校准",
    "draft": "未校准",
    "needs_review": "待复核",
}

# 来源列**整列待裁**（2026-08-29 真跑立案）：provenance.source 现状是获取回路的审计叙事
# （含内部落点编号、方法论语言、旁证推理），语域不适合逐字上纸；渲染层禁改写、禁静默逐条取舍，
# 故页脚暂只渲三项纯结构化事实（名称/取数时间/校准状态），来源的上纸形态等裁决
# （候选：获取侧拆 citation 与 audit_note 两字段改源）。经验条目"经验判断、无外部标准背书"
# 的说明话术随来源列一并待裁（原设计挂在来源列上）。立案明细见
# _iteration/run-2026-08-29-first-visible-report/。

_CSS = """
@page { size: A4; margin: 18mm; }
body { font-family: "Songti SC", "Noto Serif CJK SC", serif; color: #1a1a1a;
       margin: 0; line-height: 1.7; }
.sheet { max-width: 174mm; margin: 0 auto; padding: 12mm 0; }
.sheet { page-break-after: always; }
.cover { text-align: center; padding-top: 60mm; }
.cover h1 { font-size: 28pt; letter-spacing: 0.2em; margin-bottom: 8mm; }
.cover .meta { color: #555; font-size: 10.5pt; }
.toc h2, .chapter h2 { font-size: 16pt; border-bottom: 1px solid #999; padding-bottom: 2mm; }
.toc ol { font-size: 12pt; }
.card { margin: 6mm 0; }
.card h3 { font-size: 12pt; margin: 0 0 1.5mm; }
.card p { margin: 0; font-size: 11pt; }
.locked-texts { margin-top: 8mm; }
.locked-text { font-size: 10pt; color: #333; border-left: 3px solid #999;
               padding: 1mm 3mm; margin: 2mm 0; }
.provenance { margin-top: 8mm; border-top: 1px dashed #999; padding-top: 2mm;
              font-size: 9pt; color: #555; }
.provenance h4 { margin: 0 0 1mm; font-size: 9.5pt; }
.provenance ul { margin: 0; padding-left: 5mm; }
.pending { background: #f2f2f2; border-bottom: 1px dotted #999; }
"""


@dataclass
class RenderResult:
    html: str
    page_count: int
    card_count: int
    # (page_id, 锁定文案 ID)：要求挂载但数据里无正文（待补录）——缺席即少说，逐条记录供核对。
    missing_locked_texts: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _esc(text: str) -> str:
    return html.escape(text, quote=False)


def _render_text(text: str, anchors_by_id: dict[str, ReportAnchor]) -> str:
    # 先转义再替换：占位符不含转义字符，正文里的标签字符则必须在替换前就地失效。
    return replace_placeholders(_esc(text), anchors_by_id)


def _provenance_line(note: ProvenanceNote, anchors_by_id: dict[str, ReportAnchor]) -> str:
    anchor = anchors_by_id.get(note.lkp_id)
    if anchor is None:
        raise RenderError([f"依据标注引用的落点 {note.lkp_id} 在数据包 anchors 中不存在"])
    label = _CALIBRATION_LABELS.get(note.calibration)
    if label is None:
        raise RenderError([f"落点 {note.lkp_id} 校准状态不认识：{note.calibration!r}"])
    parts = [f"<strong>{_esc(anchor.name)}</strong>"]
    if note.effective_from or note.effective_to:
        span = f"{note.effective_from or '—'} 至 {note.effective_to or '长期'}"
        parts.append(f"取数时间：{_esc(span)}")
    parts.append(f"状态：{label}")
    return "<li>" + "，".join(parts) + "</li>"


def _render_page(
    page: Page,
    anchors_by_id: dict[str, ReportAnchor],
    locked_texts: dict[str, str],
    result: RenderResult,
) -> str:
    title = DOMAIN_TITLES.get(page.domain)
    if title is None:
        title = page.domain
        result.warnings.append(f"域 {page.domain} 无章题展示名，按原名渲出")

    out: list[str] = [f'<section class="sheet chapter"><h2>{_esc(title)}</h2>']
    for card in page.cards:
        out.append('<article class="card">')
        out.append(f"<h3>{_render_text(card.thesis, anchors_by_id)}</h3>")
        out.append(f"<p>{_render_text(card.body, anchors_by_id)}</p>")
        out.append("</article>")
        result.card_count += 1

    rendered_locked = [t for t in page.locked_text_ids if t in locked_texts]
    for text_id in page.locked_text_ids:
        if text_id not in locked_texts:
            result.missing_locked_texts.append((page.page_id, text_id))
    if rendered_locked:
        out.append('<div class="locked-texts">')
        for text_id in rendered_locked:
            # 逐字输出、独立成块：禁拼接（"接到句子后面"也算）、禁改写。
            out.append(f'<p class="locked-text">{_esc(locked_texts[text_id])}</p>')
        out.append("</div>")

    if page.provenance_notes:
        out.append('<footer class="provenance"><h4>本页依据</h4><ul>')
        for note in page.provenance_notes:
            out.append(_provenance_line(note, anchors_by_id))
        out.append("</ul></footer>")

    out.append("</section>")
    return "\n".join(out)


def render_book(
    pages: list[Page],
    package: RenderPackage,
    locked_texts: dict[str, str],
) -> RenderResult:
    """整册渲染。任一页失败即整册失败（RenderError 上抛，与成文线"任一域失败整册失败"同哲学）。"""
    result = RenderResult(html="", page_count=len(pages), card_count=0)
    anchors_by_id = package.anchors_by_id()

    chapters = [_render_page(p, anchors_by_id, locked_texts, result) for p in pages]

    toc_items = "".join(f"<li>{_esc(DOMAIN_TITLES.get(p.domain, p.domain))}</li>" for p in pages)
    meta = (
        f'<p class="meta">数据基准日：{_esc(package.evaluated_on)}</p>'
        if package.evaluated_on
        else ""
    )
    doc = (
        "<!doctype html>\n"
        '<html lang="zh-CN"><head><meta charset="utf-8">'
        "<title>装修设计报告</title>"
        f"<style>{_CSS}</style></head><body>\n"
        f'<section class="sheet cover"><h1>装修设计报告</h1>{meta}</section>\n'
        f'<section class="sheet toc"><h2>目录</h2><ol>{toc_items}</ol></section>\n'
        + "\n".join(chapters)
        + "\n</body></html>\n"
    )

    # 出口自检（渲染层自己的红线，不是重判成文质量）：内部编号绝不进客户产物。
    if "lkp-" in doc:
        raise RenderError(["渲染产物含 lkp- 内部编号（客户语域禁内部编号），拒绝出册"])

    result.html = doc
    return result
