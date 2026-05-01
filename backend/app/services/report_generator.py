from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER

from app.schemas import ContractAnalysis, ClauseCategory, MissingClauseRelevance, RiskLevel

RISK_COLOR = {
    RiskLevel.HIGH:   colors.HexColor("#DC2626"),
    RiskLevel.MEDIUM: colors.HexColor("#D97706"),
    RiskLevel.LOW:    colors.HexColor("#16A34A"),
}
RISK_BG = {
    RiskLevel.HIGH:   colors.HexColor("#FEE2E2"),
    RiskLevel.MEDIUM: colors.HexColor("#FEF3C7"),
    RiskLevel.LOW:    colors.HexColor("#DCFCE7"),
}
CATEGORY_COLOR = {
    "Best Practice":       colors.HexColor("#16A34A"),
    "Acceptable Standard": colors.HexColor("#2563EB"),
    "Minor Improvement":   colors.HexColor("#D97706"),
    "Moderate Risk":       colors.HexColor("#EA580C"),
    "High Risk":           colors.HexColor("#DC2626"),
    "Critical Risk":       colors.HexColor("#7F1D1D"),
}
RELEVANCE_COLOR = {
    "Essential":              colors.HexColor("#DC2626"),
    "Recommended":            colors.HexColor("#D97706"),
    "Optional / Not Required": colors.HexColor("#16A34A"),
}

DISCLAIMER = (
    "DISCLAIMER: This report provides AI-generated contract risk analysis for informational "
    "purposes only and does not constitute legal advice. Always consult a qualified legal "
    "professional before making decisions based on this analysis."
)


def generate_report(analysis: ContractAnalysis, filename: str) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    def h1(text):
        return Paragraph(text, ParagraphStyle("H1r", parent=styles["Heading1"], spaceAfter=4))

    def h2(text):
        return Paragraph(text, ParagraphStyle("H2r", parent=styles["Heading2"], spaceAfter=4))

    def h3(text):
        return Paragraph(text, ParagraphStyle("H3r", parent=styles["Heading3"], spaceAfter=2))

    def body(text):
        return Paragraph(text, styles["Normal"])

    def small(text, color=None):
        s = ParagraphStyle("sm", parent=styles["Normal"], fontSize=8, leading=12)
        if color:
            return Paragraph(f'<font color="{color.hexval()}">{text}</font>', s)
        return Paragraph(text, s)

    def label(text):
        return Paragraph(text, ParagraphStyle("lbl", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold"))

    def gap(h=0.3):
        return Spacer(1, h * cm)

    def hr():
        return HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey)

    disclaimer_style = ParagraphStyle(
        "Disc", parent=styles["Normal"], fontSize=8,
        backColor=colors.HexColor("#FEF9C3"), borderColor=colors.HexColor("#CA8A04"),
        borderWidth=1, borderPadding=6, textColor=colors.HexColor("#713F12"),
    )

    # ── Title ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Contract Risk Analysis Report",
                            ParagraphStyle("Title", parent=styles["Title"], fontSize=20, spaceAfter=4)))
    story.append(body(f"Document: {filename}"))
    story.append(body(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"))
    story.append(body(f"Perspective: {analysis.analysis_perspective}"))
    story.append(gap(0.3))
    story.append(Paragraph(DISCLAIMER, disclaimer_style))
    story.append(gap(0.5))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(gap(0.3))

    # ── A. Executive Summary ───────────────────────────────────────────────
    story.append(h1("A. Executive Summary"))
    rc = RISK_COLOR[analysis.overall_risk_level]

    score_data = [
        ["Risk Score", "Risk Level", "Recommendation"],
        [
            Paragraph(f'<font color="{rc.hexval()}"><b>{analysis.overall_risk_score}/100</b></font>', styles["Normal"]),
            Paragraph(f'<font color="{rc.hexval()}"><b>{analysis.overall_risk_level.value}</b></font>', styles["Normal"]),
            Paragraph(f'<b>{analysis.final_recommendation}</b>', styles["Normal"]),
        ],
    ]
    st = Table(score_data, colWidths=[5 * cm, 4 * cm, 7.5 * cm])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [RISK_BG[analysis.overall_risk_level]]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(st)
    story.append(gap(0.4))
    story.append(h2("Assessment"))
    story.append(body(analysis.document_summary))
    story.append(gap(0.3))

    # Quality summary table
    if analysis.quality_summary:
        qs = analysis.quality_summary
        q_data = [
            ["Dimension", "Assessment"],
            ["Legal Structure", qs.overall_legal_structure],
            ["Commercial Balance", qs.commercial_balance],
            ["Drafting Clarity", qs.drafting_clarity],
            ["Enforceability Confidence", qs.enforceability_confidence],
            ["Negotiation Readiness", qs.negotiation_readiness],
        ]
        qt = Table(q_data, colWidths=[8 * cm, 8.5 * cm])
        qt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(h2("Contract Quality Summary"))
        story.append(qt)
        story.append(gap(0.3))

    story.append(hr())
    story.append(gap(0.3))

    # ── B. Main Findings ──────────────────────────────────────────────────
    story.append(h1("B. Main Findings"))

    if analysis.main_risks:
        story.append(h2("True Risks"))
        for r in analysis.main_risks:
            story.append(small(f'<font color="#DC2626">• {r}</font>'))
        story.append(gap(0.2))

    if analysis.minor_improvements:
        story.append(h2("Minor Improvements"))
        for m in analysis.minor_improvements:
            story.append(small(f'<font color="#D97706">• {m}</font>'))
        story.append(gap(0.2))

    if analysis.best_practice_clauses:
        story.append(h2("Best-Practice Clauses"))
        for b in analysis.best_practice_clauses:
            story.append(small(f'<font color="#16A34A">• {b}</font>'))
        story.append(gap(0.2))

    story.append(hr())
    story.append(gap(0.3))

    # ── C. Missing Clauses ────────────────────────────────────────────────
    story.append(h1("C. Missing Clauses"))
    if analysis.missing_clauses:
        mc_data = [["Clause Type", "Classification", "Reason"]]
        for mc in analysis.missing_clauses:
            rel_color = RELEVANCE_COLOR.get(mc.relevance.value, colors.grey)
            mc_data.append([
                mc.clause_type,
                Paragraph(f'<font color="{rel_color.hexval()}"><b>{mc.relevance.value}</b></font>',
                          ParagraphStyle("mc", parent=styles["Normal"], fontSize=8)),
                Paragraph(mc.reason, ParagraphStyle("mc2", parent=styles["Normal"], fontSize=8)),
            ])
        mc_table = Table(mc_data, colWidths=[4 * cm, 4.5 * cm, 8 * cm])
        mc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
        ]))
        story.append(mc_table)
    else:
        story.append(body("No standard clauses are missing."))
    story.append(gap(0.3))
    story.append(hr())
    story.append(gap(0.3))

    # ── D. Cross-Clause Logic Review ──────────────────────────────────────
    story.append(h1("D. Cross-Clause Logic Review"))
    if analysis.contradictions:
        detail_s = ParagraphStyle("dc", parent=styles["Normal"], fontSize=8, leading=12)
        label_s = ParagraphStyle("dl", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold")
        for c in analysis.contradictions:
            sc = RISK_COLOR[c.severity]
            involved = c.clause_a_title + (f" ↔ {c.clause_b_title}" if c.clause_b_title else " (self-defeating)")
            block = [
                Paragraph(f'<font color="{sc.hexval()}"><b>[{c.severity.value}] {c.contradiction_type}</b></font> — {involved}', label_s),
                Paragraph(c.description, detail_s),
                Paragraph(f"<i>Impact: {c.impact}</i>", detail_s),
                gap(0.15),
            ]
            story.append(KeepTogether(block))
    else:
        story.append(body("No material cross-clause contradictions detected."))
    story.append(gap(0.3))
    story.append(hr())
    story.append(gap(0.3))

    # ── E. Clause-by-Clause Review ────────────────────────────────────────
    story.append(h1("E. Clause-by-Clause Review"))
    story.append(gap(0.2))

    # Summary table
    tbl_data = [["#", "Clause", "Category", "Score", "Affects"]]
    for i, clause in enumerate(analysis.clauses, 1):
        cat_color = CATEGORY_COLOR.get(clause.category.value, colors.grey)
        tbl_data.append([
            str(i),
            clause.clause_title,
            Paragraph(f'<font color="{cat_color.hexval()}"><b>{clause.category.value}</b></font>',
                      ParagraphStyle("ct", parent=styles["Normal"], fontSize=7)),
            str(clause.risk_score),
            clause.affected_party.value,
        ])
    summary_tbl = Table(tbl_data, colWidths=[0.8 * cm, 5.5 * cm, 4.5 * cm, 1.5 * cm, 3 * cm])
    summary_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A5F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F9FAFB"), colors.white]),
    ]))
    story.append(summary_tbl)
    story.append(gap(0.4))

    # Detailed clause blocks
    detail_style = ParagraphStyle("det", parent=styles["Normal"], fontSize=8, leading=12)
    label_style = ParagraphStyle("lbl2", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold")

    for i, clause in enumerate(analysis.clauses, 1):
        cat_color = CATEGORY_COLOR.get(clause.category.value, colors.grey)
        enforceability_note = (
            [Paragraph('<font color="#7C3AED"><b>Enforceability Concern:</b> This clause may be unenforceable as written.</font>', detail_style)]
            if clause.enforceability_concern else []
        )
        what_works = (
            [label("What Works Well:"), Paragraph(clause.what_works_well, detail_style)]
            if clause.what_works_well and clause.what_works_well.lower() not in ("none", "n/a", "") else []
        )
        issue_text = clause.risk_explanation or ""
        issue_block = (
            [label("Issue:"), Paragraph(issue_text, detail_style)]
            if issue_text and issue_text.lower() not in ("none", "") else []
        )
        rev_text = clause.suggested_revision or ""
        revision_block = (
            [label("Suggested Revision:"), Paragraph(rev_text, detail_style)]
            if rev_text and rev_text.lower() not in ("none required", "none", "") else []
        )

        block = [
            Paragraph(
                f'<b>{i}. {clause.clause_title}</b>'
                f' — <font color="{cat_color.hexval()}">{clause.category.value}</font>'
                f' [{clause.risk_score}/100] — Affects: {clause.affected_party.value}',
                styles["Heading3"]
            ),
            *enforceability_note,
            label("Original Text:"),
            Paragraph(clause.original_text, detail_style),
            *what_works,
            *issue_block,
            *revision_block,
            label("Negotiation Advice:"),
            Paragraph(clause.negotiation_advice, detail_style),
            gap(0.3),
            hr(),
            gap(0.2),
        ]
        story.append(KeepTogether(block))

    # ── F. Final Recommendation ───────────────────────────────────────────
    story.append(h1("F. Final Recommendation"))
    story.append(body(f"<b>{analysis.final_recommendation}</b>"))
    story.append(gap(0.5))
    story.append(Paragraph(DISCLAIMER, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
