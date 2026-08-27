from __future__ import annotations

from typing import Any

from app.schemas.schemas import ProcurementDocType
from app.services.procurement_templates import get_procurement_sections


def procurement_guidance(doc_type: ProcurementDocType) -> str:
    sections = get_procurement_sections(doc_type)
    titles = ", ".join(s.title for s in sections)
    return f"Procurement document type '{doc_type.value}' requiring standard sections: {titles}."


def _text_node(text: str, bold: bool = False) -> dict[str, Any]:
    return {
        "type": "text",
        "text": text,
        "detail": 0,
        "format": 1 if bold else 0,
        "mode": "normal",
        "style": "",
        "version": 1,
    }


def heading_node(text: str, tag: str = "h1") -> dict[str, Any]:
    return {
        "type": "heading",
        "tag": tag,
        "children": [_text_node(text)],
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "version": 1,
    }


def paragraph_node(text: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "children": [_text_node(text)],
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "version": 1,
        "style": "",
    }


def compliance_warning_node(text: str, note: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "children": [
            _text_node("⚠️ COMPLIANCE WARNING: ", bold=True),
            _text_node(f"{note} - {text}"),
        ],
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "version": 1,
        "style": "background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 8px 12px; margin: 8px 0; border-radius: 4px; color: #92400e;",
    }


def approved_clause_node(text: str, title: str) -> dict[str, Any]:
    return {
        "type": "paragraph",
        "children": [
            _text_node(f"🔒 APPROVED CLAUSE ({title}): ", bold=True),
            _text_node(text),
        ],
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "version": 1,
        "style": "background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 8px 12px; margin: 8px 0; border-radius: 4px; color: #065f46;",
    }


def bullet_list_node(items: list[str]) -> dict[str, Any]:
    return {
        "type": "list",
        "listType": "bullet",
        "tag": "ul",
        "start": 1,
        "children": [
            {
                "type": "listitem",
                "value": index + 1,
                "children": [_text_node(item)],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "version": 1,
            }
            for index, item in enumerate(items)
        ],
        "direction": "ltr",
        "format": "",
        "indent": 0,
        "version": 1,
    }


def table_cell_node(text: str, is_header: bool = False) -> dict[str, Any]:
    return {
        "type": "tablecell",
        "children": [
            {
                "type": "paragraph",
                "children": [_text_node(text, bold=is_header)],
                "direction": "ltr",
                "format": "",
                "indent": 0,
                "version": 1,
            }
        ],
        "headerState": 1 if is_header else 0,
        "version": 1,
    }


def table_row_node(cells: list[str], is_header: bool = False) -> dict[str, Any]:
    return {
        "type": "tablerow",
        "children": [table_cell_node(cell, is_header=is_header) for cell in cells],
        "version": 1,
    }


def table_node(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    table_children = [table_row_node(headers, is_header=True)]
    for row in rows:
        table_children.append(table_row_node(row, is_header=False))

    return {
        "type": "table",
        "children": table_children,
        "version": 1,
    }


def page_break_node() -> dict[str, Any]:
    return {
        "type": "horizontalrule",
        "version": 1,
    }


def build_document_root(page_nodes: list[list[dict[str, Any]]]) -> dict[str, Any]:
    children: list[dict[str, Any]] = []
    for index, nodes in enumerate(page_nodes):
        if index > 0:
            children.append(page_break_node())
        children.extend(nodes)

    return {
        "root": {
            "type": "root",
            "children": children,
            "direction": "ltr",
            "format": "",
            "indent": 0,
            "version": 1,
        }
    }
