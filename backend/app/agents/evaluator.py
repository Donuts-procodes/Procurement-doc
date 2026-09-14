from __future__ import annotations

import logging
import re
import time
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("gdocs.evaluator")


class ToolAuditEntry(BaseModel):
    """Audit record for a single tool invocation by a subagent."""
    agent_name: str
    tool_name: str
    latency_ms: float = 0
    token_input: int = 0
    token_output: int = 0
    source_relevance: float = Field(default=1.0, ge=0.0, le=1.0, description="How relevant the tool's output was to the task (0=irrelevant, 1=perfect)")
    success: bool = True
    error: str | None = None


class EvaluationReport(BaseModel):
    """Aggregated execution quality report across all subagent tool invocations."""
    reward_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Normalized quality score: 0.0 (poor) to 1.0 (excellent)")
    total_tool_calls: int = 0
    total_latency_ms: float = 0
    total_tokens: int = 0
    efficiency_grade: str = "A"
    agent_scores: dict[str, float] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ExecutionEvaluator:
    """ponytail: Lightweight execution evaluator that grades subagent tool trajectories.
    No ML model needed — deterministic scoring based on latency, token economy,
    source relevance, and reconciliation accuracy."""

    def __init__(self) -> None:
        self._audit_log: list[ToolAuditEntry] = []

    def record(self, entry: ToolAuditEntry) -> None:
        self._audit_log.append(entry)

    def record_simple(
        self,
        agent_name: str,
        tool_name: str,
        latency_ms: float = 0,
        tokens: int = 0,
        relevance: float = 1.0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        self._audit_log.append(ToolAuditEntry(
            agent_name=agent_name,
            tool_name=tool_name,
            latency_ms=latency_ms,
            token_input=tokens,
            source_relevance=relevance,
            success=success,
            error=error,
        ))

    def evaluate(self, audit_report: dict[str, Any] | None = None) -> EvaluationReport:
        """Score the execution trajectory and generate recommendations."""
        if not self._audit_log:
            return EvaluationReport()

        total_calls = len(self._audit_log)
        total_latency = sum(e.latency_ms for e in self._audit_log)
        total_tokens = sum(e.token_input + e.token_output for e in self._audit_log)
        success_rate = sum(1 for e in self._audit_log if e.success) / total_calls
        avg_relevance = sum(e.source_relevance for e in self._audit_log) / total_calls

        # Per-agent scoring
        agent_entries: dict[str, list[ToolAuditEntry]] = {}
        for entry in self._audit_log:
            agent_entries.setdefault(entry.agent_name, []).append(entry)

        agent_scores: dict[str, float] = {}
        for agent, entries in agent_entries.items():
            a_success = sum(1 for e in entries if e.success) / len(entries)
            a_relevance = sum(e.source_relevance for e in entries) / len(entries)
            agent_scores[agent] = round(a_success * 0.4 + a_relevance * 0.6, 3)

        # Composite reward score
        reward = round(success_rate * 0.3 + avg_relevance * 0.4 + min(1.0, 5000 / max(total_latency, 1)) * 0.3, 3)

        # Grade thresholds
        if reward >= 0.9:
            grade = "A"
        elif reward >= 0.75:
            grade = "B"
        elif reward >= 0.6:
            grade = "C"
        else:
            grade = "D"

        flags: list[str] = []
        recommendations: list[str] = []

        if success_rate < 0.8:
            flags.append(f"High failure rate: {1 - success_rate:.0%} of tool calls failed")
            recommendations.append("Investigate failing tool calls; consider fallback strategies")

        if avg_relevance < 0.6:
            flags.append(f"Low source relevance: avg {avg_relevance:.2f}")
            recommendations.append("Research subagent may need tighter query scoping or KB enrichment")

        if total_latency > 30000:
            flags.append(f"High total latency: {total_latency:.0f}ms")
            recommendations.append("Consider reducing parallel worker count or optimizing LLM calls")

        # Cross-check with fact-check audit report
        if audit_report:
            if audit_report.get("status") == "FLAGGED":
                flags.append("Fact-check audit flagged discrepancies")
                reward = max(0.0, reward - 0.15)
            conflicts = audit_report.get("conflicts", [])
            if conflicts:
                flags.extend([f"Audit conflict: {c}" for c in conflicts[:3]])

        report = EvaluationReport(
            reward_score=max(0.0, min(1.0, reward)),
            total_tool_calls=total_calls,
            total_latency_ms=round(total_latency, 1),
            total_tokens=total_tokens,
            efficiency_grade=grade,
            agent_scores=agent_scores,
            flags=flags,
            recommendations=recommendations,
        )

        logger.info(
            f"📊 Execution Evaluator: Reward={report.reward_score}, Grade={report.efficiency_grade}, "
            f"Calls={total_calls}, Latency={total_latency:.0f}ms, Flags={len(flags)}"
        )
        return report

    def clear(self) -> None:
        self._audit_log.clear()

    @property
    def audit_log(self) -> list[ToolAuditEntry]:
        return list(self._audit_log)


class DocumentAuditReport(BaseModel):
    """Quality verification report comparing the generated document with source files and enterprise standards."""
    score: float = Field(default=100.0, ge=0.0, le=100.0)
    passed: bool = True
    critical_defects: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class DocumentQualityAuditor:
    """Automated Critic & Quality Gate.
    Verifies that the generated document preserves grounded source tables,
    strictly adheres to H1/H2 hierarchical numbering, places diagrams contextually without collisions,
    and doesn't pollute administrative sections with technical flowcharts.
    """

    def audit(
        self,
        segments: list[Any],
        source_tables: list[dict[str, Any]] | None = None,
        source_text: str | None = None,
    ) -> DocumentAuditReport:
        defects: list[str] = []
        warnings: list[str] = []
        score = 100.0

        if not segments:
            return DocumentAuditReport(score=0.0, passed=False, critical_defects=["No document segments generated."])

        admin_keywords = ["submission", "instructions", "eligibility", "evaluation", "criteria", "terms", "conditions", "clause", "scoring"]

        for idx, seg in enumerate(segments, start=1):
            content_dict = seg.content if isinstance(seg.content, dict) else (getattr(seg, "content", {}) or {})
            nodes = content_dict.get("content", []) if isinstance(content_dict, dict) else []
            if not nodes:
                continue

            # A. First node must be H1 heading
            if nodes[0].get("type") != "heading" or nodes[0].get("attrs", {}).get("level") != 1:
                defects.append(f"Segment {idx} ('{seg.name}') does not begin with an H1 heading (found {nodes[0].get('type')}).")
                score -= 20.0

            # B. Diagram count per section
            diagrams = [
                n for n in nodes
                if n.get("type") == "image" and "unsplash.com" not in n.get("attrs", {}).get("src", "")
            ]
            if len(diagrams) > 1:
                defects.append(f"Segment {idx} ('{seg.name}') has {len(diagrams)} diagram images stacked.")
                score -= 15.0

            # C. Administrative section diagram pollution
            sec_lower = (seg.name or "").lower()
            if any(k in sec_lower for k in admin_keywords) and diagrams:
                defects.append(f"Administrative section '{seg.name}' contains misplaced technical diagram.")
                score -= 20.0

            # D. Subheading numbering hierarchy
            for n in nodes:
                if n.get("type") == "heading" and n.get("attrs", {}).get("level") == 2:
                    sub_txt = "".join(c.get("text", "") for c in n.get("content", []) if isinstance(c, dict)).strip()
                    if not sub_txt.startswith(f"{idx}."):
                        defects.append(f"Subheading '{sub_txt}' in Segment {idx} does not follow main section numbering '{idx}.'.")
                        score -= 10.0

            # E. Diagram figure caption presence
            for i, n in enumerate(nodes):
                if n.get("type") == "image":
                    has_caption = False
                    if i + 1 < len(nodes):
                        nxt = nodes[i + 1]
                        nxt_txt = "".join(c.get("text", "") for c in nxt.get("content", []) if isinstance(c, dict)).strip()
                        if nxt_txt.startswith("Figure:"):
                            has_caption = True
                    if not has_caption:
                        defects.append(f"Image in Segment {idx} ('{seg.name}') is missing a descriptive figure caption.")
                        score -= 5.0

            # F. Topic-to-Diagram Semantic Alignment Check
            for i, n in enumerate(nodes):
                if n.get("type") == "image" and "unsplash.com" not in n.get("attrs", {}).get("src", ""):
                    cap_text = ""
                    if i + 1 < len(nodes):
                        nxt = nodes[i + 1]
                        nxt_txt = "".join(c.get("text", "") for c in nxt.get("content", []) if isinstance(c, dict)).strip()
                        if nxt_txt.startswith("Figure:"):
                            cap_text = nxt_txt[7:].strip()
                    if not cap_text:
                        cap_text = n.get("attrs", {}).get("alt", "")

                    cap_lower = cap_text.lower()
                    sec_lower = (seg.name or "").lower()

                    # Onboarding / Setup diagram in Timeline section
                    if any(k in cap_lower for k in ["setup", "onboard", "pairing", "qr code", "activation", "sim", "whitelist"]) and \
                       any(k in sec_lower for k in ["timeline", "milestones", "schedule", "deadlines", "calendar"]):
                        defects.append(f"Diagram '{cap_text}' (Technical Setup/Onboarding) does not match section topic '{seg.name}' (Project Timeline).")
                        score -= 25.0

                    # Architecture diagram in Timeline or Admin or Financial section
                    if any(k in cap_lower for k in ["architecture", "infrastructure", "data flow", "gateway"]) and \
                       any(k in sec_lower for k in ["timeline", "pricing", "budget", "payment", "milestone", "deadlines", "evaluation", "criteria"]):
                        defects.append(f"Technical architecture diagram '{cap_text}' misplaced in non-technical section '{seg.name}'.")
                        score -= 25.0

            # G. Unresolved Placeholder & Generic Dummy Token Audit
            for n in nodes:
                node_text = ""
                if n.get("type") in ("paragraph", "heading"):
                    node_text = "".join(c.get("text", "") for c in n.get("content", []) if isinstance(c, dict))
                elif n.get("type") in ("bulletList", "orderedList"):
                    for item in n.get("content", []):
                        for p in item.get("content", []):
                            node_text += " " + "".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
                
                if node_text:
                    ph_match = re.search(r'\[(?:TBD|Insert\b|Company Name|Vendor Name|Pending Review|TODO\b|Place[ -]?holder)[^\]]*\]', node_text, re.IGNORECASE)
                    if ph_match:
                        defects.append(f"Unresolved placeholder '{ph_match.group(0)}' detected in Segment {idx} ('{seg.name}').")
                        score -= 15.0
                    dummy_match = re.search(r'\b(?:John Doe|Acme Corp|Lorem Ipsum)\b', node_text, re.IGNORECASE)
                    if dummy_match:
                        defects.append(f"Generic dummy entity '{dummy_match.group(0)}' detected in Segment {idx} ('{seg.name}').")
                        score -= 15.0

        # 2. Duplicate Table Audit Across Segments & Table Integrity Check
        seen_table_headers: dict[tuple[str, ...], tuple[int, str]] = {}
        for idx, seg in enumerate(segments, start=1):
            content_dict = seg.content if isinstance(seg.content, dict) else (getattr(seg, "content", {}) or {})
            nodes = content_dict.get("content", []) if isinstance(content_dict, dict) else []
            for n in nodes:
                if n.get("type") == "table":
                    t_rows = n.get("content", [])
                    if len(t_rows) <= 1:
                        defects.append(f"Empty table with zero data rows detected in Segment {idx} ('{seg.name}').")
                        score -= 15.0
                        continue
                    
                    header_row = t_rows[0].get("content", [])
                    hdr_cells: list[str] = []
                    for c in header_row:
                        cell_p = c.get("content", [{}])[0] if c.get("content") else {}
                        hdr_txt = "".join(t.get("text", "") for t in cell_p.get("content", []) if isinstance(t, dict)).strip()
                        hdr_cells.append(hdr_txt)
                    
                    hdr_tuple = tuple(hdr_cells)
                    if hdr_tuple and len(hdr_tuple) >= 2:
                        if hdr_tuple in seen_table_headers:
                            prev_idx, prev_name = seen_table_headers[hdr_tuple]
                            defects.append(
                                f"Duplicate table detected: Table headers {list(hdr_tuple)} in Segment {idx} ('{seg.name}') duplicate identical table from Segment {prev_idx} ('{prev_name}')."
                            )
                            score -= 25.0
                        else:
                            seen_table_headers[hdr_tuple] = (idx, seg.name)

        # 3. Grounded Source Table Preservation Audit
        if source_tables:
            total_doc_tables = sum(
                1 for seg in segments
                if isinstance(getattr(seg, "content", None), dict)
                and any(n.get("type") == "table" for n in seg.content.get("content", []))
            )
            if total_doc_tables == 0 and len(source_tables) > 0:
                defects.append(f"Source file contains {len(source_tables)} rich grounded tables, but 0 were included in generated document.")
                score -= 25.0

        # 4. Source Content Fidelity Audit — checks that key entities/terms from source appear in generated output
        fidelity_ratio = 1.0
        if source_text and len(source_text) > 200:
            # Extract key terms: organization names, budget figures, technology names, dates, percentages
            source_key_terms: set[str] = set()

            # Named numeric values (budgets, SLAs, percentages)
            for m in re.finditer(r'\$[\d,]+(?:\.\d{2})?', source_text):
                source_key_terms.add(m.group(0))
            for m in re.finditer(r'\d{1,3}(?:\.\d+)?%', source_text):
                source_key_terms.add(m.group(0))

            # Capitalized multi-word proper nouns (organization/product names) — 2+ capitalized words in sequence
            for m in re.finditer(r'(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', source_text):
                term = m.group(0).strip()
                # Filter out generic section headings and very short matches
                if len(term) > 6 and term.lower() not in {"the following", "this section", "in addition", "for example"}:
                    source_key_terms.add(term)

            # Technology/protocol names (uppercase acronyms 2-6 chars)
            for m in re.finditer(r'\b[A-Z]{2,6}\b', source_text):
                term = m.group(0)
                # Filter common English words that happen to be uppercase
                if term not in {"THE", "AND", "FOR", "NOT", "BUT", "WITH", "FROM", "THIS", "THAT", "WILL", "ARE", "HAS", "WAS", "ALL", "CAN"}:
                    source_key_terms.add(term)

            # Specific date patterns
            for m in re.finditer(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', source_text):
                source_key_terms.add(m.group(0))

            if source_key_terms:
                # Build full text of generated document for matching
                generated_full_text = ""
                for seg in segments:
                    content_dict = seg.content if isinstance(seg.content, dict) else (getattr(seg, "content", {}) or {})
                    nodes = content_dict.get("content", []) if isinstance(content_dict, dict) else []
                    for n in nodes:
                        if n.get("type") in ("paragraph", "heading"):
                            generated_full_text += " " + "".join(c.get("text", "") for c in n.get("content", []) if isinstance(c, dict))
                        elif n.get("type") in ("bulletList", "orderedList"):
                            for item in n.get("content", []):
                                for p in item.get("content", []):
                                    generated_full_text += " " + "".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
                        elif n.get("type") == "table":
                            for row in n.get("content", []):
                                for cell in row.get("content", []):
                                    for cp in cell.get("content", []):
                                        generated_full_text += " " + "".join(c.get("text", "") for c in cp.get("content", []) if isinstance(c, dict))

                matched = sum(1 for t in source_key_terms if t in generated_full_text)
                total_terms = len(source_key_terms)
                fidelity_ratio = matched / total_terms if total_terms > 0 else 1.0

                logger.info(
                    f"🔍 Source Fidelity Check: {matched}/{total_terms} key terms matched "
                    f"(fidelity={fidelity_ratio:.1%})"
                )

                if fidelity_ratio < 0.3:
                    defects.append(f"Critical source fidelity gap: only {matched}/{total_terms} ({fidelity_ratio:.0%}) key source terms appear in the generated document.")
                    score -= 20.0
                elif fidelity_ratio < 0.5:
                    defects.append(f"Low source fidelity: only {matched}/{total_terms} ({fidelity_ratio:.0%}) key source terms appear in the generated document.")
                    score -= 10.0
                elif fidelity_ratio < 0.7:
                    warnings.append(f"Moderate source fidelity: {matched}/{total_terms} ({fidelity_ratio:.0%}) key source terms appear in the generated document. Consider enriching KB retrieval.")

        score = max(0.0, min(100.0, score))
        passed = score >= 85.0 and len(defects) == 0

        logger.info(
            f"🔍 Document Quality Auditor: Score={score:.1f}, Passed={passed}, "
            f"Defects={len(defects)}, Warnings={len(warnings)}, SourceFidelity={fidelity_ratio:.1%}"
        )

        return DocumentAuditReport(
            score=score,
            passed=passed,
            critical_defects=defects,
            warnings=warnings,
            recommendations=[f"Fix: {d}" for d in defects],
        )

