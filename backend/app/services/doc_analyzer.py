from __future__ import annotations

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from app.schemas.dynamic_template_schemas import DynamicParsedSection


class DocAnalyzer:
    """
    Robust, fully dynamic document parser for .docx and .md.
    Extracts structured headings, styled sections, embedded tables, and guidance
    without third-party C-dependencies.
    """

    NS = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    @classmethod
    def parse_docx_bytes(cls, content: bytes) -> tuple[str, str, list[DynamicParsedSection]]:
        """Extracts title, subtitle, and sections from DOCX package XML."""
        if not content:
            return "Untitled Document", "", []

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                if "word/document.xml" not in z.namelist():
                    return "Untitled Document", "", []
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
        except Exception:
            return "Untitled Document", "", []

        paragraphs_data: list[dict[str, Any]] = []

        # Iterate over both paragraphs (<w:p>) and tables (<w:tbl>) in document order
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            
            if tag == "p":
                # Check style for Heading / Title
                is_heading_style = False
                is_title_style = False
                p_style = elem.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle")
                if p_style is not None:
                    style_val = p_style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "").lower()
                    if "heading" in style_val or "header" in style_val:
                        is_heading_style = True
                    elif "title" in style_val:
                        is_title_style = True

                # Check bold
                is_bold = elem.find(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}b") is not None

                # Extract text runs
                texts = [t.text for t in elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
                p_text = "".join(texts).strip()

                if p_text:
                    paragraphs_data.append({
                        "type": "p",
                        "text": p_text,
                        "is_heading": is_heading_style,
                        "is_title": is_title_style,
                        "is_bold": is_bold,
                    })

            elif tag == "tbl":
                # Extract tabular data
                rows: list[list[str]] = []
                for row_elem in elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                    row_cells: list[str] = []
                    for cell_elem in row_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                        cell_texts = [t.text for t in cell_elem.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if t.text]
                        row_cells.append("".join(cell_texts).strip())
                    if any(row_cells):
                        rows.append(row_cells)

                if rows:
                    table_summary = " | ".join(rows[0])
                    paragraphs_data.append({
                        "type": "tbl",
                        "text": f"Table ({len(rows)} rows): {table_summary}",
                        "is_heading": False,
                        "is_title": False,
                        "is_bold": False,
                    })

        if not paragraphs_data:
            return "Untitled Document", "", []

        # Derive Document Title
        doc_title = paragraphs_data[0]["text"]
        doc_subtitle = ""
        body_start_idx = 1

        if len(paragraphs_data) > 1 and len(paragraphs_data[1]["text"]) < 140:
            # Check if second line is a subtitle
            if not paragraphs_data[1]["is_heading"] and not paragraphs_data[1]["text"].startswith(("1.", "1)", "##")):
                doc_subtitle = paragraphs_data[1]["text"]
                body_start_idx = 2

        sections: list[DynamicParsedSection] = []
        heading_re = re.compile(r"^(\d+[\.\)]|[A-Z][A-Za-z0-9\s\&]{3,50}:?|#+)\s*(.+)$")

        current_title = "Executive Overview"
        current_body: list[str] = []
        has_table = False

        for item in paragraphs_data[body_start_idx:]:
            txt = item["text"]
            is_tbl = item["type"] == "tbl"

            if is_tbl:
                has_table = True
                current_body.append(txt)
                continue

            # Detect section boundary
            is_section_header = (
                item["is_heading"] or
                (item["is_bold"] and len(txt) < 80 and not txt.endswith(".")) or
                bool(heading_re.match(txt) and len(txt) < 90 and not txt.endswith("."))
            )

            if is_section_header:
                if current_body:
                    sec_type = cls._classify_section_type(current_title, " ".join(current_body), has_table)
                    sections.append(
                        DynamicParsedSection(
                            title=current_title,
                            section_type=sec_type,
                            guidance=" ".join(current_body)[:300],
                            estimated_pages=1.0,
                        )
                    )
                    current_body = []
                    has_table = False

                match = heading_re.match(txt)
                current_title = match.group(2).strip() if match else txt
            else:
                if any(w in txt.lower() for w in ["price", "cost", "sku", "qty", "rate", "$", "eur", "usd"]):
                    has_table = True
                current_body.append(txt)

        # Flush trailing section
        if current_title:
            sec_type = cls._classify_section_type(current_title, " ".join(current_body), has_table)
            sections.append(
                DynamicParsedSection(
                    title=current_title,
                    section_type=sec_type,
                    guidance=" ".join(current_body)[:300],
                    estimated_pages=1.0,
                )
            )

        if not sections:
            sections.append(
                DynamicParsedSection(
                    title="Main Content",
                    section_type="prose",
                    guidance="Parsed document specifications.",
                    estimated_pages=1.0,
                )
            )

        return doc_title, doc_subtitle, sections

    @classmethod
    def parse_markdown_text(cls, text: str) -> tuple[str, str, list[DynamicParsedSection]]:
        """Extracts structure from markdown files."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return "Untitled Markdown", "", []

        # Remove optional YAML frontmatter if present
        start_idx = 0
        if lines[0] == "---":
            for i in range(1, len(lines)):
                if lines[i] == "---":
                    start_idx = i + 1
                    break
        clean_lines = lines[start_idx:]
        if not clean_lines:
            return "Untitled Markdown", "", []

        doc_title = clean_lines[0].lstrip("#").strip()
        doc_subtitle = ""
        sections: list[DynamicParsedSection] = []

        current_title = "Overview"
        current_body: list[str] = []
        has_table = False

        for line in clean_lines[1:]:
            if line.startswith("#"):
                if current_body:
                    sections.append(
                        DynamicParsedSection(
                            title=current_title,
                            section_type=cls._classify_section_type(current_title, " ".join(current_body), has_table),
                            guidance=" ".join(current_body)[:300],
                            estimated_pages=1.0,
                        )
                    )
                    current_body = []
                    has_table = False
                current_title = line.lstrip("#").strip()
            else:
                if "|" in line:
                    has_table = True
                current_body.append(line)

        if current_title:
            sections.append(
                DynamicParsedSection(
                    title=current_title,
                    section_type=cls._classify_section_type(current_title, " ".join(current_body), has_table),
                    guidance=" ".join(current_body)[:300],
                    estimated_pages=1.0,
                )
            )

        return doc_title, doc_subtitle, sections

    @classmethod
    def _classify_section_type(cls, title: str, text: str, has_tables: bool) -> str:
        """Classifies section rendering pattern (prose, line_items, payment_schedule, clause)."""
        combined = f"{title} {text}".lower()
        if has_tables or any(w in combined for w in ["pricing", "cost model", "line items", "bill of materials", "sku", "rates", "costing", "commercials"]):
            return "line_items"
        if any(w in combined for w in ["milestone", "schedule", "payment terms", "deliverables timeline", "allocation"]):
            return "payment_schedule"
        if any(w in combined for w in ["clause", "warranty", "indemnity", "confidentiality", "compliance", "regulatory", "sla", "terms", "mandates"]):
            return "clause"
        return "prose"
