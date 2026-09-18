from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field
from app.schemas.schemas import ProcurementDocType


class PreflightBlueprintRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    prompt: str = Field(default="Generate procurement proposal document")
    kb_id: str | None = Field(default=None)
    current_template_id: str | None = Field(default=None)
    current_doc_type: str | None = Field(default=None)
    session_id: str | None = Field(default=None)


class PreflightGuidedParams(BaseModel):
    buyer_name: str | None = Field(default=None)
    vendor_name: str | None = Field(default=None)
    budget_estimate: str | None = Field(default=None)
    delivery_timeline: str | None = Field(default=None)
    target_dates: str | None = Field(default=None, description="Requested booking/event/delivery dates")
    room_or_facility: str | None = Field(default=None, description="Requested room, venue, or facility space")
    availability_verification: str = Field(
        default="Manual Staff Verification",
        description="Bypasses automated date/room collision algorithms in favor of manual staff auditing",
    )
    primary_tech: str | None = Field(default=None)
    compliance_frameworks: list[str] = Field(default_factory=list)
    sla_target: str = Field(default="99.9% (Standard)")


class PreflightSectionOutline(BaseModel):
    index: int
    title: str
    section_type: str
    guidance: str


class PreflightBlueprintResponse(BaseModel):
    recommended_template_id: str
    recommended_doc_type: ProcurementDocType
    template_title: str
    template_icon: str
    confidence_score: float
    match_reason: str
    recommended_num_pages: int
    guided_params: PreflightGuidedParams
    outline_sections: list[PreflightSectionOutline]
    detected_keywords: list[str]
