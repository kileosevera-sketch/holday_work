"""Historical reports, batch queries, and executive export routes (in-memory store)."""
import csv
import io
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse

from store import store

router = APIRouter(tags=["Historical Reports & Exports"])


def _build_csv_content(rows: List[Dict[str, Any]]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        "id", "filename", "feedback_text", "sentiment", "sentiment_score",
        "severity", "severity_priority", "predicted_cause", "prediction_confidence",
        "detected_symptoms", "created_at"
    ])
    for r in rows:
        writer.writerow([
            r.get("id"),
            r.get("filename"),
            r.get("feedback_text"),
            r.get("sentiment"),
            r.get("sentiment_score"),
            r.get("severity"),
            r.get("severity_priority"),
            r.get("predicted_cause"),
            f"{r.get('prediction_confidence')}%",
            "; ".join(r.get("detected_symptoms") or []),
            r.get("created_at") or "",
        ])
    return "\ufeff" + buffer.getvalue()


def _filtered_records(batch_id: Optional[str], filename: Optional[str]) -> List[Dict[str, Any]]:
    records = list(reversed(store.all_records()))  # newest first
    if isinstance(batch_id, str) and batch_id.strip():
        val = batch_id.strip()
        matching_reports = [r["id"] for r in store.all_reports()
                            if r["batch_id"] == val or str(r["id"]) == val]
        records = [r for r in records
                   if r.get("batch_id") == val or r.get("report_id") in matching_reports]
    if isinstance(filename, str) and filename.strip():
        records = [r for r in records if r.get("filename") == filename.strip()]
    return records


# ---------------------------------------------------------------------------
# 1. STATIC EXPORT & REPORT DOWNLOAD ROUTES (MUST BE DECLARED FIRST)
# ---------------------------------------------------------------------------

@router.get("/api/reports/feedback.csv")
@router.get("/api/feedback/export/")
def export_feedback_csv(
    batch_id: Optional[str] = Query(default=None),
    filename: Optional[str] = Query(default=None),
):
    """Export analyzed feedback as CSV with UTF-8 BOM for Microsoft Excel compatibility."""
    items = _filtered_records(batch_id, filename)
    csv_text = _build_csv_content(items)
    out_name = f"feedback-export-{batch_id}.csv" if batch_id else "feedback-export.csv"
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )


@router.get("/api/reports/feedback.xlsx")
def export_feedback_xlsx(
    batch_id: Optional[str] = Query(default=None),
    filename: Optional[str] = Query(default=None),
):
    """Export analyzed feedback records in Excel-compatible spreadsheet format."""
    items = _filtered_records(batch_id, filename)
    csv_text = _build_csv_content(items)
    out_name = f"feedback-report-{batch_id or 'all'}.csv"
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )


def _aggregate_snapshot(records=None):
    """Shared aggregation used by the HTML and PDF executive reports."""
    if records is None:
        records = store.all_records()
    total = len(records)

    sent_map: Dict[str, int] = {}
    sev_map: Dict[str, int] = {}
    cause_map: Dict[str, int] = {}
    per_day: Dict[str, int] = {}
    for r in records:
        sent_map[str(r["sentiment"]).lower()] = sent_map.get(str(r["sentiment"]).lower(), 0) + 1
        sev_map[str(r["severity"]).lower()] = sev_map.get(str(r["severity"]).lower(), 0) + 1
        c = r.get("predicted_cause") or "unknown"
        cause_map[c] = cause_map.get(c, 0) + 1
        day = (r.get("service_date") or r.get("created_at") or "")[:10]
        if day:
            per_day[day] = per_day.get(day, 0) + 1

    cause_rows = sorted(cause_map.items(), key=lambda kv: kv[1], reverse=True)
    daily_rows = sorted(per_day.items())[-15:]
    return total, sent_map, sev_map, cause_rows, daily_rows


@router.get("/api/reports/executive-summary.html", response_class=HTMLResponse)
def get_executive_summary_html():
    """
    Renders a comprehensive, visually rich Executive Analysis Summary Report with embedded
    histogram charts, KPI summaries, and root cause distributions designed for printing or saving as PDF.
    """
    total, sent_map, sev_map, cause_rows, daily_rows = _aggregate_snapshot()
    critical_count = sev_map.get("critical", 0) + sev_map.get("high", 0)

    # Generate SVG Histogram for Daily Volume
    max_daily = max([c for _, c in daily_rows] or [1])
    bars_svg = ""
    bar_width = 36
    gap = 14
    for idx, (day_val, count) in enumerate(daily_rows):
        h = max(8, int((count / max_daily) * 160))
        x = idx * (bar_width + gap) + 40
        y = 190 - h
        day_str = str(day_val)[5:]  # MM-DD
        bars_svg += f"""
        <g class="bar-group">
            <rect x="{x}" y="{y}" width="{bar_width}" height="{h}" rx="5" fill="#6F4530" />
            <text x="{x + bar_width/2}" y="{y - 8}" text-anchor="middle" font-size="11" font-weight="bold" fill="#3B1F12">{count}</text>
            <text x="{x + bar_width/2}" y="210" text-anchor="middle" font-size="10" fill="#64748b">{day_str}</text>
        </g>
        """

    svg_chart = f"""
    <svg width="{len(daily_rows) * (bar_width + gap) + 80}" height="230" style="max-width: 100%;">
        <line x1="20" y1="190" x2="{len(daily_rows) * (bar_width + gap) + 60}" y2="190" stroke="#E2E8F0" stroke-width="2"/>
        {bars_svg}
    </svg>
    """

    # Generate Top Causes Rows
    causes_html = ""
    for idx, (cause, count) in enumerate(cause_rows[:8]):
        pct = round((count / (total or 1)) * 100, 1)
        causes_html += f"""
        <tr>
            <td style="padding: 10px; font-weight: bold; color: #3B1F12;">#{idx + 1}</td>
            <td style="padding: 10px; font-weight: 600;">{cause.replace('_', ' ')}</td>
            <td style="padding: 10px; text-align: center; font-weight: bold; color: #6F4530;">{count}</td>
            <td style="padding: 10px; text-align: right;">
                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 8px;">
                    <div style="width: 100px; height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden;">
                        <div style="width: {pct}%; height: 100%; background: #6F4530;"></div>
                    </div>
                    <span style="font-size: 12px; font-weight: bold;">{pct}%</span>
                </div>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>AI Post-Sales Customer Intelligence - Executive Analysis Report</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px auto; max-width: 900px; color: #1e293b; background: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #E2E8F0; padding-bottom: 20px; }}
            .title {{ font-size: 24px; font-weight: 800; color: #3B1F12; margin: 0; }}
            .subtitle {{ font-size: 13px; color: #64748B; margin-top: 5px; }}
            .btn-print {{ background: #6F4530; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; }}
            .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 25px 0; }}
            .kpi-card {{ border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; background: #FDFBF7; }}
            .kpi-label {{ font-size: 11px; text-transform: uppercase; font-weight: bold; color: #64748B; }}
            .kpi-value {{ font-size: 26px; font-weight: 800; color: #3B1F12; margin: 8px 0 0; }}
            .section {{ border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; margin-bottom: 25px; }}
            .section-title {{ font-size: 16px; font-weight: 800; color: #3B1F12; margin: 0 0 15px; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
            th {{ text-align: left; padding: 8px 10px; border-bottom: 2px solid #CBD5E1; color: #64748B; font-size: 11px; text-transform: uppercase; }}
            td {{ border-bottom: 1px solid #F1F5F9; }}
            @media print {{
                .btn-print {{ display: none; }}
                body {{ margin: 0; padding: 15px; max-width: 100%; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1 class="title">Customer Intelligence: Post-Sales Analysis & Failure Prediction</h1>
                <p class="subtitle">Comprehensive Technical Summary Report · Generated from In-Memory Analysis Archive</p>
            </div>
            <button class="btn-print" onclick="window.print()">Print / Save as PDF</button>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Ingested Feedback</div>
                <div class="kpi-value">{total}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Positive Sentiment</div>
                <div class="kpi-value" style="color: #2e7d32;">{sent_map.get('positive', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Negative Complaints</div>
                <div class="kpi-value" style="color: #c62828;">{sent_map.get('negative', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Critical / High Alerts</div>
                <div class="kpi-value" style="color: #d97706;">{critical_count}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Feedback Volume Timeline (Daily Complaint Spike Histogram)</h2>
            <p style="font-size: 12px; color: #64748B; margin-top: -10px; margin-bottom: 15px;">Visualizing complaint frequency by service date to detect emerging failure surges.</p>
            {svg_chart}
        </div>

        <div class="section">
            <h2 class="section-title">Ranked Technical Failure Causes & Recurrence Likelihood</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Predicted Failure Cause</th>
                        <th style="text-align: center;">Feedback Count</th>
                        <th style="text-align: right;">Proportion (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {causes_html}
                </tbody>
            </table>
        </div>

        <div style="font-size: 11px; color: #94A3B8; text-align: center; margin-top: 30px;">
            AI Post-Sales Feedback Intelligence Engine · Automated Quality Assurance & Failure Prediction
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# 2. PDF ANALYSIS REPORT (MUST BE BEFORE DYNAMIC {report_identifier} ROUTE)
# ---------------------------------------------------------------------------

@router.get("/api/reports/analysis-report.pdf")
def download_pdf_report(batch_id: Optional[str] = Query(default=None)):
    """Generate and download a comprehensive PDF analysis report using ReportLab."""
    try:
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.platypus import (
            HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ReportLab is not installed. Run: pip install reportlab",
        )

    if batch_id:
        records = _filtered_records(batch_id, None)
        total, sent_map, sev_map, cause_rows, daily_rows = _aggregate_snapshot(records)
    else:
        total, sent_map, sev_map, cause_rows, daily_rows = _aggregate_snapshot()
    cause_rows = cause_rows[:10]

    # ── Colour palette ───────────────────────────────────────────────────────
    BROWN      = rl_colors.HexColor("#6F4530")
    TAN        = rl_colors.HexColor("#C08A5B")
    DEEP_BROWN = rl_colors.HexColor("#3B1F12")
    TEAL       = rl_colors.HexColor("#52706A")
    CREAM      = rl_colors.HexColor("#FBF6F0")
    LIGHT_TAN  = rl_colors.HexColor("#F3E6D7")
    SLATE      = rl_colors.HexColor("#64748B")
    POS_GREEN  = rl_colors.HexColor("#2E7D32")
    NEG_RED    = rl_colors.HexColor("#C62828")
    WARN_AMB   = rl_colors.HexColor("#D97706")
    WHITE      = rl_colors.white
    GRID_LINE  = rl_colors.HexColor("#E2E8F0")

    # ── Styles ───────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=20, textColor=DEEP_BROWN, spaceAfter=4, leading=24,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=10, textColor=SLATE, spaceAfter=16,
    )
    section_style = ParagraphStyle(
        "SectionHead", parent=styles["Heading2"],
        fontSize=13, textColor=DEEP_BROWN, spaceBefore=18, spaceAfter=6,
        borderPad=4,
    )
    note_style = ParagraphStyle(
        "Note", parent=styles["Normal"],
        fontSize=9, textColor=SLATE, spaceAfter=8,
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=SLATE, alignment=1,
    )

    # ── Build document ───────────────────────────────────────────────────────
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="AI Post-Sales Feedback Analysis Report",
        author="Customer Intelligence Engine",
    )

    story = []
    W = A4[0] - 4 * cm  # usable page width

    # ── Header ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Customer Intelligence: Post-Sales Analysis &amp; Failure Prediction", title_style))
    story.append(Paragraph(
        f"Comprehensive AI Analysis Report · Generated {datetime.now().strftime('%d %B %Y, %H:%M')}",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=BROWN, spaceAfter=14))

    # ── KPI summary row ───────────────────────────────────────────────────────
    critical_count = sev_map.get("critical", 0) + sev_map.get("high", 0)
    kpi_data = [
        ["Total Feedback", "Positive", "Negative", "High / Critical Alerts"],
        [str(total), str(sent_map.get("positive", 0)),
         str(sent_map.get("negative", 0)), str(critical_count)],
    ]
    kpi_table = Table(kpi_data, colWidths=[W / 4] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), BROWN),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("BACKGROUND",  (0, 1), (-1, 1), CREAM),
        ("FONTNAME",    (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 1), (-1, 1), 18),
        ("TEXTCOLOR",   (0, 1), (0, 1), DEEP_BROWN),
        ("TEXTCOLOR",   (1, 1), (1, 1), POS_GREEN),
        ("TEXTCOLOR",   (2, 1), (2, 1), NEG_RED),
        ("TEXTCOLOR",   (3, 1), (3, 1), WARN_AMB),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",        (0, 0), (-1, -1), 0.5, GRID_LINE),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 16))

    # ── Section 1: Sentiment Distribution ────────────────────────────────────
    story.append(Paragraph("1 · Sentiment Distribution", section_style))
    story.append(Paragraph(
        "NLP VADER analysis classifies each feedback record as Positive, Neutral, or Negative, "
        "enabling quality teams to monitor customer satisfaction at a glance.",
        note_style,
    ))

    sent_order = [("positive", POS_GREEN, "Positive"),
                  ("neutral",  TAN,       "Neutral"),
                  ("negative", NEG_RED,   "Negative")]
    sent_header = [["Sentiment", "Count", "Share (%)"]]
    sent_body = []
    for key, _color, label in sent_order:
        count = sent_map.get(key, 0)
        pct = round((count / (total or 1)) * 100, 1)
        sent_body.append([label, str(count), f"{pct}%"])

    sent_table = Table(sent_header + sent_body, colWidths=[W * 0.55, W * 0.2, W * 0.25])
    sent_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ALIGN",       (1, 0), (2, -1), "CENTER"),
        ("GRID",        (0, 0), (-1, -1), 0.4, GRID_LINE),
        ("TOPPADDING",  (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sent_table)
    story.append(Spacer(1, 14))

    def build_bar_chart(labels, values, color, chart_title, chart_height=185):
        drawing = Drawing(W, chart_height)
        chart = VerticalBarChart()
        chart.x = 42
        chart.y = 34
        chart.width = W - 54
        chart.height = chart_height - 58
        chart.data = [values]
        chart.categoryAxis.categoryNames = labels
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.angle = 25
        chart.categoryAxis.labels.dy = -8
        chart.valueAxis.valueMin = 0
        chart.valueAxis.valueMax = max(values or [0]) * 1.15 or 1
        chart.valueAxis.valueStep = max(1, int(chart.valueAxis.valueMax / 5))
        chart.valueAxis.labels.fontName = "Helvetica"
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.strokeColor = GRID_LINE
        chart.categoryAxis.strokeColor = GRID_LINE
        chart.bars[0].fillColor = color
        chart.bars[0].strokeColor = color
        chart.barSpacing = 4
        drawing.add(String(0, chart_height - 12, chart_title, fontName="Helvetica-Bold", fontSize=9, fillColor=DEEP_BROWN))
        drawing.add(chart)
        return drawing

    story.append(Paragraph("Sentiment Distribution Chart", section_style))
    story.append(build_bar_chart(
        [label for _, _, label in sent_order],
        [sent_map.get(key, 0) for key, _, _ in sent_order],
        TEAL,
        "Feedback records by sentiment",
    ))
    story.append(Spacer(1, 12))

    # ── Section 2: Severity Prioritization ───────────────────────────────────
    story.append(Paragraph("2 · Severity Prioritization Matrix", section_style))
    story.append(Paragraph(
        "Each feedback item is rated by urgency. Critical and High items are escalated for immediate "
        "engineering review and quality assurance action.",
        note_style,
    ))

    sev_order = [("critical", NEG_RED,  "Critical"),
                 ("high",     WARN_AMB, "High"),
                 ("medium",   TAN,      "Medium"),
                 ("low",      TEAL,     "Low")]
    sev_header = [["Priority Level", "Count", "Share (%)", "Action Required"]]
    sev_actions = {
        "critical": "Immediate escalation & root-cause investigation",
        "high":     "Engineering review within 24 hours",
        "medium":   "Schedule for next sprint / QA cycle",
        "low":      "Monitor; log for pattern analysis",
    }
    sev_body = []
    for key, _color, label in sev_order:
        count = sev_map.get(key, 0)
        pct = round((count / (total or 1)) * 100, 1)
        sev_body.append([label, str(count), f"{pct}%", sev_actions[key]])

    sev_table = Table(sev_header + sev_body, colWidths=[W * 0.22, W * 0.10, W * 0.10, W * 0.58])
    sev_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), BROWN),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ALIGN",       (1, 0), (2, -1), "CENTER"),
        ("GRID",        (0, 0), (-1, -1), 0.4, GRID_LINE),
        ("TOPPADDING",  (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(sev_table)
    story.append(Spacer(1, 14))

    # ── Section 3: Ranked Failure Causes ─────────────────────────────────────
    story.append(Paragraph("3 · Ranked Failure Causes &amp; Recurrence Likelihood", section_style))
    story.append(Paragraph(
        "AI Bayesian root-cause ranking maps customer-reported symptoms to the most probable "
        "underlying technical failure, ordered by frequency across all ingested feedback.",
        note_style,
    ))

    cause_header = [["Rank", "Predicted Failure Cause", "Count", "%"]]
    cause_body = []
    for idx, (cause, count) in enumerate(cause_rows):
        pct = round((count / (total or 1)) * 100, 1)
        cause_body.append([
            f"#{idx + 1}",
            (cause or "unknown").replace("_", " ").title(),
            str(count),
            f"{pct}%",
        ])

    cause_table = Table(
        cause_header + cause_body,
        colWidths=[W * 0.08, W * 0.58, W * 0.17, W * 0.17],
    )
    cause_style = [
        ("BACKGROUND",    (0, 0), (-1, 0), DEEP_BROWN),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("FONTSIZE",      (0, 1), (-1, -1), 8),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
        ("ALIGN",         (2, 0), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRID_LINE),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]
    cause_table.setStyle(TableStyle(cause_style))
    story.append(cause_table)
    story.append(Spacer(1, 14))

    # ── Section 4: Daily Feedback Volume Histogram ────────────────────────────
    story.append(Paragraph("4 · Daily Feedback Volume Histogram", section_style))
    story.append(Paragraph(
        "Complaint volume per day based on service/feedback dates. Sudden spikes indicate "
        "emerging failure events that require early-warning escalation.",
        note_style,
    ))

    if daily_rows:
        story.append(build_bar_chart(
            [str(day)[5:] for day, _ in daily_rows],
            [count for _, count in daily_rows],
            BROWN,
            "Feedback volume by service date",
            chart_height=205,
        ))
    else:
        story.append(Paragraph("No dated feedback records available for the daily chart.", note_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=GRID_LINE, spaceAfter=8))
    story.append(Paragraph(
        "AI Post-Sales Feedback Intelligence Engine · Automated Quality Assurance &amp; Failure Prediction · "
        f"Report generated {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        footer_style,
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()

    filename = "analysis-report.pdf"
    if batch_id:
        safe_batch_id = "".join(
            character for character in batch_id if character.isalnum() or character in "-_."
        )
        filename = f"analysis-report-{safe_batch_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 3. DYNAMIC & PARAMETERIZED REPORT ROUTES
# ---------------------------------------------------------------------------

@router.get("/api/reports")
def list_reports(
    search: str = Query(default="", description="Search reports by filename or batch ID"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Search and list past system uploads and batch reports.
    Provides metadata, record counts, and timestamps for historical tracking.
    """
    reports = store.all_reports()
    if isinstance(search, str) and search.strip():
        pattern = search.strip().lower()
        reports = [r for r in reports
                   if pattern in r["filename"].lower() or pattern in r["batch_id"].lower()]
    reports.reverse()  # newest first

    total = len(reports)
    page = reports[offset:offset + limit]

    def _to_dict(r: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": r["id"],
            "batch_id": r["batch_id"],
            "filename": r["filename"],
            "file_type": r["file_type"],
            "total_feedback_count": r["total_feedback_count"],
            "analyzed_feedback_count": r["analyzed_feedback_count"],
            "critical_count": r["critical_count"],
            "duplicate_records_skipped": r["duplicate_records_skipped"],
            "invalid_rows_skipped": r["invalid_rows_skipped"],
            "summary_metrics": r.get("summary_metrics") or {},
            "trend_metrics": r.get("trend_metrics") or [],
            "root_cause_ranking": r.get("root_cause_ranking") or [],
            "future_forecasts": r.get("future_forecasts") or {},
            "status": r["status"],
            "uploaded_at": r["uploaded_at"],
        }

    return {"items": [_to_dict(r) for r in page], "total": total, "limit": limit, "offset": offset}


@router.get("/api/batches")
def list_batches():
    """Frontend-compatible batches endpoint for dashboard integration."""
    reports = reversed(store.all_reports())  # newest first
    return {
        "batches": [
            {
                "id": r["batch_id"],
                "report_id": r["id"],
                "filename": r["filename"],
                "feedback_count": r["analyzed_feedback_count"],
                "uploaded_at": r["uploaded_at"],
                "critical_count": r["critical_count"],
                "duplicate_records_skipped": r["duplicate_records_skipped"],
            }
            for r in reports
        ]
    }


@router.get("/api/reports/{report_identifier}")
def get_report_detail(report_identifier: str):
    """
    Retrieve a specific historical analysis layout for side-by-side comparison.
    Accepts either an integer ID or batch_id string.
    """
    report = None
    for r in store.all_reports():
        if report_identifier.isdigit() and r["id"] == int(report_identifier):
            report = r
            break
        if r["batch_id"] == report_identifier:
            report = r
            break

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_identifier}' not found in archive.",
        )

    items = store.batch_records(report["id"])[:50]

    detail = {
        "id": report["id"],
        "batch_id": report["batch_id"],
        "filename": report["filename"],
        "file_type": report["file_type"],
        "total_feedback_count": report["total_feedback_count"],
        "analyzed_feedback_count": report["analyzed_feedback_count"],
        "critical_count": report["critical_count"],
        "duplicate_records_skipped": report["duplicate_records_skipped"],
        "invalid_rows_skipped": report["invalid_rows_skipped"],
        "summary_metrics": report.get("summary_metrics") or {},
        "trend_metrics": report.get("trend_metrics") or [],
        "root_cause_ranking": report.get("root_cause_ranking") or [],
        "future_forecasts": report.get("future_forecasts") or {},
        "status": report["status"],
        "uploaded_at": report["uploaded_at"],
        "sample_records": items,
    }
    return detail
