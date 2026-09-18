from __future__ import annotations

import hashlib
from app.schemas.dynamic_template_schemas import (
    CardAspectRatio,
    TemplateCategoryEnum,
    VisualThemeModel,
)


class ThemeSynthesizer:
    """Derives deterministic visual themes, gradients, and aspect ratios from document metadata."""

    THEME_PALETTES: dict[TemplateCategoryEnum, list[tuple[str, str, str]]] = {
        TemplateCategoryEnum.MARKETING: [
            ("#EA580C", "#F97316", "linear-gradient(180deg, #F97316 0%, #C2410C 100%)"),
            ("#E11D48", "#FB7185", "linear-gradient(135deg, #E11D48 0%, #BE123C 100%)"),
            ("#BE185D", "#F472B6", "linear-gradient(135deg, #DB2777 0%, #9D174D 100%)"),
        ],
        TemplateCategoryEnum.BUSINESS: [
            ("#2563EB", "#60A5FA", "linear-gradient(180deg, #1D4ED8 0%, #1E40AF 100%)"),
            ("#0284C7", "#38BDF8", "linear-gradient(135deg, #0284C7 0%, #0369A1 100%)"),
            ("#0D9488", "#2DD4BF", "linear-gradient(135deg, #0F766E 0%, #115E59 100%)"),
        ],
        TemplateCategoryEnum.REPORTS_ANALYSIS: [
            ("#7C3AED", "#A78BFA", "linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%)"),
            ("#D97706", "#FBBF24", "linear-gradient(180deg, #F59E0B 0%, #D97706 100%)"),
            ("#9333EA", "#C084FC", "linear-gradient(135deg, #6B21A8 0%, #4C1D95 100%)"),
        ],
        TemplateCategoryEnum.LEGAL_FORMS: [
            ("#0F172A", "#64748B", "linear-gradient(180deg, #334155 0%, #0F172A 100%)"),
            ("#1E293B", "#94A3B8", "linear-gradient(135deg, #1E293B 0%, #0F172A 100%)"),
        ],
        TemplateCategoryEnum.EDUCATION: [
            ("#059669", "#34D399", "linear-gradient(135deg, #059669 0%, #047857 100%)"),
            ("#0891B2", "#22D3EE", "linear-gradient(135deg, #0E7490 0%, #155E75 100%)"),
        ],
        TemplateCategoryEnum.CAREER_PORTFOLIO: [
            ("#4F46E5", "#818CF8", "linear-gradient(135deg, #4F46E5 0%, #3730A3 100%)"),
        ],
        TemplateCategoryEnum.CUSTOM: [
            ("#334155", "#64748B", "linear-gradient(135deg, #334155 0%, #1E293B 100%)"),
            ("#475569", "#94A3B8", "linear-gradient(180deg, #475569 0%, #1E293B 100%)"),
        ],
    }

    @classmethod
    def infer_category(cls, title: str, text_sample: str) -> TemplateCategoryEnum:
        """Classifies document category using semantic keywords."""
        content = f"{title} {text_sample}".lower()
        if any(w in content for w in ["marketing", "campaign", "pitch", "creative", "proposal", "advertising"]):
            return TemplateCategoryEnum.MARKETING
        if any(w in content for w in ["contract", "clause", "nda", "terms", "legal", "sla", "indemnity", "statutory"]):
            return TemplateCategoryEnum.LEGAL_FORMS
        if any(w in content for w in ["analysis", "analytics", "dashboard", "metric", "report", "scorecard", "evaluation"]):
            return TemplateCategoryEnum.REPORTS_ANALYSIS
        if any(w in content for w in ["handbook", "training", "guide", "education", "orientation", "onboarding", "culture"]):
            return TemplateCategoryEnum.EDUCATION
        if any(w in content for w in ["resume", "portfolio", "career", "profile", "cv"]):
            return TemplateCategoryEnum.CAREER_PORTFOLIO
        return TemplateCategoryEnum.BUSINESS

    @classmethod
    def infer_aspect_ratio(cls, section_count: int, category: TemplateCategoryEnum) -> CardAspectRatio:
        """Determines card geometry based on section complexity and category."""
        if category == TemplateCategoryEnum.MARKETING:
            return CardAspectRatio.TALL_POSTER
        if category == TemplateCategoryEnum.REPORTS_ANALYSIS and section_count <= 3:
            return CardAspectRatio.LANDSCAPE_CARD
        return CardAspectRatio.PORTRAIT_A4

    @classmethod
    def generate_theme(cls, doc_id: str, category: TemplateCategoryEnum) -> VisualThemeModel:
        """Deterministically assigns gradient palette and badges using doc_id hash."""
        palettes = cls.THEME_PALETTES.get(category) or cls.THEME_PALETTES[TemplateCategoryEnum.BUSINESS]
        idx = int(hashlib.md5(doc_id.encode("utf-8")).hexdigest(), 16) % len(palettes)
        primary, accent, gradient = palettes[idx]

        badge_map = {
            TemplateCategoryEnum.MARKETING: "Campaign",
            TemplateCategoryEnum.BUSINESS: "Corporate",
            TemplateCategoryEnum.REPORTS_ANALYSIS: "Analysis",
            TemplateCategoryEnum.LEGAL_FORMS: "Legal / SLA",
            TemplateCategoryEnum.EDUCATION: "Guide",
            TemplateCategoryEnum.CAREER_PORTFOLIO: "Portfolio",
            TemplateCategoryEnum.CUSTOM: "Auto-Parsed",
        }

        return VisualThemeModel(
            primary_color=primary,
            accent_color=accent,
            gradient_css=gradient,
            badge_text=badge_map.get(category, "Document"),
            badge_color=primary,
            dark_mode_compatible=True,
        )

