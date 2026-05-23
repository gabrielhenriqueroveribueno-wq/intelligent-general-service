# IGS — Intelligent General Service
# Copyright (c) 2026 — All Rights Reserved
# Proprietary Software — Unauthorized use prohibited. See LICENSE.
# Origin fingerprint: IGS-2026-BR-ANCHIETA-BILLIE-WHATSAPP-SAAS
"""
Serviço de geração de boleto em PDF usando ReportLab.

Gera um PDF simples com dados do boleto para envio via WhatsApp.
"""

import io
import logging
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)


def generate_boleto_pdf(
    student_name: str,
    registration_number: str,
    course: str,
    reference_month: str,
    amount: Decimal,
    due_date: date | None,
    barcode: str | None = None,
    institution_name: str = "Faculdade Anchieta",
) -> bytes:
    """
    Gera PDF do boleto com dados do aluno.

    Returns:
        Bytes do arquivo PDF.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    header_style = ParagraphStyle(
        "header", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1B3A5C")
    )
    elements.append(Paragraph(institution_name, header_style))
    elements.append(Spacer(1, 0.3 * cm))

    sub_style = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10, textColor=colors.grey)
    elements.append(Paragraph("Boleto de Mensalidade", sub_style))
    elements.append(Spacer(1, 1 * cm))

    # Dados do aluno
    data = [
        ["Aluno:", student_name],
        ["RA:", registration_number],
        ["Curso:", course],
        ["Referencia:", reference_month],
        ["Valor:", f"R$ {amount:,.2f}"],
        ["Vencimento:", due_date.strftime("%d/%m/%Y") if due_date else "N/A"],
    ]

    if barcode:
        data.append(["Cod. Barras:", barcode])

    table = Table(data, colWidths=[4 * cm, 12 * cm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, -1), (-1, -1), 1, colors.HexColor("#1B3A5C")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 1 * cm))

    # Instruções
    info_style = ParagraphStyle(
        "info", parent=styles["Normal"], fontSize=9, textColor=colors.grey, leading=14
    )
    elements.append(
        Paragraph(
            "Este documento e apenas um comprovante. Para pagamento, utilize o codigo "
            "de barras acima ou acesse o portal do aluno.",
            info_style,
        )
    )
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(
        Paragraph(
            f"Documento gerado automaticamente pelo sistema IGS - {institution_name}",
            info_style,
        )
    )

    doc.build(elements)
    return buf.getvalue()
