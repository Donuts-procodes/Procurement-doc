from __future__ import annotations

from typing import Any
from app.schemas.schemas import ProcurementDocType
from app.services.structured_tables import (
    LineItemTableData,
    PaymentScheduleData,
    compute_line_items,
    compute_payment_schedule,
)


import re

def parse_markdown_inlines(text: str) -> list[dict[str, Any]]:
    if not text:
        return [{"type": "text", "text": ""}]

    pattern = re.compile(r'(\*\*.+?\*\*|__.+?__|[*].+?[*]|_.+?_)')
    tokens = []
    last_idx = 0

    for match in pattern.finditer(text):
        start, end = match.span()
        if start > last_idx:
            plain_part = text[last_idx:start]
            if plain_part:
                tokens.append({"type": "text", "text": plain_part})

        matched_str = match.group(0)
        if matched_str.startswith("**") and matched_str.endswith("**"):
            inner = matched_str[2:-2]
            tokens.append({"type": "text", "text": inner, "marks": [{"type": "bold"}]})
        elif matched_str.startswith("__") and matched_str.endswith("__"):
            inner = matched_str[2:-2]
            tokens.append({"type": "text", "text": inner, "marks": [{"type": "bold"}]})
        elif (matched_str.startswith("*") and matched_str.endswith("*")) or (matched_str.startswith("_") and matched_str.endswith("_")):
            inner = matched_str[1:-1]
            tokens.append({"type": "text", "text": inner, "marks": [{"type": "italic"}]})
        else:
            tokens.append({"type": "text", "text": matched_str})

        last_idx = end

    if last_idx < len(text):
        remaining = text[last_idx:]
        if remaining:
            tokens.append({"type": "text", "text": remaining})

    return tokens if tokens else [{"type": "text", "text": text}]


def docx_paragraph_node(text: str, bold: bool = False) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [
            {
                "type": "text",
                "text": text,
                "marks": [{"type": "bold"}] if bold else [],
            }
        ],
    }


def tiptap_heading_node(text: str, level: int = 1) -> dict[str, Any]:
    # Strip any leading markdown '#' syntax if present
    clean_text = text.lstrip("#").strip()
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": parse_markdown_inlines(clean_text),
    }


def parse_markdown_table_str(text: str) -> dict[str, Any] | None:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    pipe_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
    if len(pipe_lines) < 2:
        return None

    # Filter out divider lines like |---|---|
    table_lines = [l for l in pipe_lines if not re.match(r"^\|[\s\-:|]+\|$", l)]
    if not table_lines:
        return None

    def split_row(row_str: str) -> list[str]:
        return [p.strip() for p in row_str.strip("|").split("|")]

    headers = split_row(table_lines[0])
    rows = [split_row(r) for r in table_lines[1:]]

    if headers and rows:
        return tiptap_table_node(headers, rows)
    return None


def tiptap_paragraph_node(text: str) -> dict[str, Any]:
    trimmed = text.strip()

    # Convert markdown pipe tables to TipTap table nodes
    if "|" in trimmed and ("\n" in trimmed or trimmed.count("|") >= 4):
        tbl = parse_markdown_table_str(trimmed)
        if tbl:
            return tbl

    # Convert markdown headings (# H1, ## H2, ### H3, #### H4) to real TipTap heading nodes
    if trimmed.startswith("#### "):
        return tiptap_heading_node(trimmed[5:].strip(), level=4)
    if trimmed.startswith("### "):
        return tiptap_heading_node(trimmed[4:].strip(), level=3)
    if trimmed.startswith("## "):
        return tiptap_heading_node(trimmed[3:].strip(), level=2)
    if trimmed.startswith("# "):
        return tiptap_heading_node(trimmed[2:].strip(), level=1)

    if trimmed.startswith(("- ", "* ", "• ")):
        bullet_text = trimmed[2:].strip()
        return tiptap_bullet_list_node([bullet_text])
    
    if re.match(r"^\d+\.\s+", trimmed):
        num_text = re.sub(r"^\d+\.\s+", "", trimmed)
        return tiptap_ordered_list_node([num_text])

    return {
        "type": "paragraph",
        "content": parse_markdown_inlines(text),
    }


def tiptap_image_node(src: str, alt: str = "Image Asset", title: str | None = None) -> dict[str, Any]:
    return {
        "type": "image",
        "attrs": {
            "src": src,
            "alt": alt,
            "title": title or alt,
        },
    }


def tiptap_compliance_warning_node(text: str, note: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "⚠️ COMPLIANCE WARNING: ", "marks": [{"type": "bold"}]},
            *parse_markdown_inlines(f"{note} - {text}"),
        ],
    }


def tiptap_approved_clause_node(text: str, title: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": f"🔒 APPROVED CLAUSE ({title}): ", "marks": [{"type": "bold"}]},
            *parse_markdown_inlines(text),
        ],
    }


def tiptap_bullet_list_node(items: list[str]) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [
            {
                "type": "listItem",
                "content": [
                    {
                        "type": "paragraph",
                        "content": parse_markdown_inlines(re.sub(r"^[-*•]\s*", "", item).strip()),
                    }
                ],
            }
            for item in items
        ],
    }


def tiptap_ordered_list_node(items: list[str]) -> dict[str, Any]:
    return {
        "type": "orderedList",
        "content": [
            {
                "type": "listItem",
                "content": [
                    {
                        "type": "paragraph",
                        "content": parse_markdown_inlines(re.sub(r"^\d+\.\s*", "", item).strip()),
                    }
                ],
            }
            for item in items
        ],
    }


def tiptap_table_cell_node(text: str, is_header: bool = False) -> dict[str, Any]:
    cell_type = "tableHeader" if is_header else "tableCell"
    parsed_nodes = parse_markdown_inlines(text)
    if is_header:
        for node in parsed_nodes:
            marks = node.setdefault("marks", [])
            if not any(m.get("type") == "bold" for m in marks):
                marks.append({"type": "bold"})

    return {
        "type": cell_type,
        "content": [
            {
                "type": "paragraph",
                "content": parsed_nodes,
            }
        ],
    }


def tiptap_table_row_node(cells: list[str], is_header: bool = False) -> dict[str, Any]:
    return {
        "type": "tableRow",
        "content": [tiptap_table_cell_node(cell, is_header=is_header) for cell in cells],
    }


def tiptap_table_node(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    table_children = [tiptap_table_row_node(headers, is_header=True)]
    for row in rows:
        table_children.append(tiptap_table_row_node(row, is_header=False))

    return {
        "type": "table",
        "content": table_children,
    }


def tiptap_callout_node(title: str, text: str, icon: str = "ℹ️") -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": f"{icon} {title}: ", "marks": [{"type": "bold"}]},
            *parse_markdown_inlines(text),
        ],
    }


def tiptap_metric_badge_node(metrics: list[tuple[str, str]]) -> dict[str, Any]:
    nodes = []
    for label, val in metrics:
        nodes.append({"type": "text", "text": f"[{label}: ", "marks": [{"type": "bold"}]})
        nodes.append({"type": "text", "text": f"{val}]  "})
    return {
        "type": "paragraph",
        "content": nodes,
    }


def tiptap_divider_node() -> dict[str, Any]:
    return {
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "────────────────────────────────────────────────────────────"}
        ],
    }


def build_tiptap_segment_doc(segment_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type": "doc",
        "content": segment_nodes,
    }
