from __future__ import annotations

from enum import Enum
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict, Field


class TemplateCategoryEnum(str, Enum):
    ALL = "all"
    MY_DOCS = "my_docs"
    EDUCATION = "education"
    BUSINESS = "business"
    REPORTS_ANALYSIS = "reports_analysis"
    MARKETING = "marketing"
    CAREER_PORTFOLIO = "career_portfolio"
    LEGAL_FORMS = "legal_forms"
    CUSTOM = "custom"


class CardAspectRatio(str, Enum):
    PORTRAIT_A4 = "portrait_a4"       # Standard vertical doc
    TALL_POSTER = "tall_poster"       # Elongated marketing flyer
    LANDSCAPE_CARD = "landscape_card" # Wide dashboard / summary
    SQUARE = "square"                 # Minimalist / Blank document


class VisualThemeModel(BaseModel):
    """CSS styling tokens generated dynamically for the document card cover."""
    model_config = ConfigDict(frozen=True)

    primary_color: str
    accent_color: str
    gradient_css: str
    badge_text: str
    badge_color: str
    dark_mode_compatible: bool = True


class DynamicParsedSection(BaseModel):
    """A section extracted dynamically from the file's headings and text."""
    model_config = ConfigDict(frozen=True)

    title: str
    section_type: str = "prose"  # prose | line_items | payment_schedule | clause
    guidance: str = ""
    estimated_pages: float = 1.0


class DynamicVisualManifest(BaseModel):
    """Complete visual manifest synthesized directly from a document file."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    subtitle: str
    category: TemplateCategoryEnum
    aspect_ratio: CardAspectRatio
    theme: VisualThemeModel
    file_name: str
    file_path: str
    source: str = "file_storage"
    is_custom: bool = True
    is_blank_doc: bool = False
    sections: Sequence[DynamicParsedSection] = Field(default_factory=list)
    tags: Sequence[str] = Field(default_factory=list)
    preview_ast: dict[str, Any] | None = None


class DynamicGalleryResponse(BaseModel):
    categories: Sequence[dict[str, str]]
    total_count: int
    templates: Sequence[DynamicVisualManifest]

