"""PDF report generation for regulator-ready case summaries."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List


def build_pdf_report(report: Dict[str, Any]) -> bytes:
    try:  # pragma: no cover - optional dependency
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF generation") from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Case {report.get('case_id') or report.get('report_id')}")
    styles = getSampleStyleSheet()
    story: List[Any] = []

    story.append(Paragraph("Regulator-Ready Fraud Report", styles["Title"]))
    story.append(Spacer(1, 12))

    sections = [
        ("Case ID", report.get("case_id") or report.get("report_id") or "-"),
        ("Risk Score", f"{float(report.get('risk_score', 0.0)):.4f}"),
        ("Confidence Score", f"{float(report.get('confidence_score', 0.0)):.4f}"),
        ("Decision", report.get("decision", "-") ),
        ("Accounts Involved", ", ".join(report.get("accounts_involved", []) or [])),
        ("Transaction Path", " -> ".join(report.get("transaction_path", []) or [])),
        ("Detected Patterns", "; ".join(report.get("detected_patterns", []) or [])),
        ("Sanctions Match", str(report.get("sanctions_screening", {}).get("matched_entity") or "None")),
        ("Jurisdiction Risk", str(report.get("jurisdiction_risk", {}).get("risk_band") or "Unknown")),
        ("Why Flagged", report.get("why_flagged") or "; ".join(report.get("reasons", []) or [])),
    ]

    for label, value in sections:
        story.append(Paragraph(f"<b>{label}:</b> {value or '-'}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    reportlab_patterns = report.get("detected_patterns", []) or []
    if reportlab_patterns:
        story.append(Paragraph("<b>Detected Patterns Detail</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        for pattern in reportlab_patterns:
            story.append(Paragraph(f"- {pattern}", styles["BodyText"]))

    doc.build(story)
    return buffer.getvalue()

