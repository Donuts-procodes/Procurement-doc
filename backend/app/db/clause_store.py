from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from app.schemas.schemas import ProcurementDocType

CLAUSE_STORE_FILE = Path(__file__).parent.parent / "data" / "clauses.json"


class ClauseEntry(BaseModel):
    id: str
    doc_type: ProcurementDocType
    section_name: str
    title: str
    body: str
    version: int = 1
    approved_by: str = "Legal Team"
    approved_at: str = "2026-01-15"


DEFAULT_APPROVED_CLAUSES: list[ClauseEntry] = [
    ClauseEntry(
        id="c1",
        doc_type=ProcurementDocType.RFQ,
        section_name="Terms & Conditions",
        title="Standard RFQ Commercial Terms",
        body="All quotations must remain valid for a minimum of ninety (90) calendar days from the submission deadline. Prices offered shall be fixed and firm for the entire contract duration, inclusive of all duties, freight, and delivery charges. Quotations omitting mandatory technical specifications will be deemed non-responsive.",
    ),
    ClauseEntry(
        id="c2",
        doc_type=ProcurementDocType.PURCHASE_ORDER,
        section_name="Payment Terms & Schedule",
        title="Standard PO Payment Policy",
        body="Invoices shall be processed on Net 30 terms following receipt and formal technical acceptance of the goods/services at the designated delivery site. All invoices must clearly reference the Purchase Order number and include line-item itemization matching this order.",
    ),
    ClauseEntry(
        id="c3",
        doc_type=ProcurementDocType.VENDOR_CONTRACT,
        section_name="Confidentiality & Intellectual Property",
        title="Standard IP & NDA Clause",
        body="Each party agrees to maintain in confidence all non-public information disclosed by the other party. All work product, deliverables, customized code, and document outputs generated under this agreement shall belong exclusively to the Purchaser as work-made-for-hire.",
    ),
    ClauseEntry(
        id="c4",
        doc_type=ProcurementDocType.VENDOR_CONTRACT,
        section_name="Liability & Indemnification",
        title="Standard Cap on Liability",
        body="Except for breaches of confidentiality or gross negligence, neither party's aggregate liability under this agreement shall exceed the total amounts paid or payable under the applicable Statement of Work in the twelve (12) months preceding the claim.",
    ),
    ClauseEntry(
        id="c5",
        doc_type=ProcurementDocType.VENDOR_CONTRACT,
        section_name="Term & Termination",
        title="Standard Termination for Convenience",
        body="Purchaser may terminate this agreement or any active SOW for convenience at any time upon thirty (30) days' written notice to Vendor. Upon termination, Purchaser shall pay Vendor for conforming services performed up to the effective termination date.",
    ),
]


class ClauseStore:
    def __init__(self) -> None:
        self.clauses: list[ClauseEntry] = list(DEFAULT_APPROVED_CLAUSES)

    def get_clause(self, doc_type: ProcurementDocType, section_name: str) -> ClauseEntry | None:
        for c in self.clauses:
            if c.doc_type == doc_type and c.section_name.lower() == section_name.lower():
                return c
        return None

    def list_clauses(self, doc_type: ProcurementDocType | None = None) -> list[ClauseEntry]:
        if doc_type:
            return [c for c in self.clauses if c.doc_type == doc_type]
        return self.clauses


clause_store = ClauseStore()
