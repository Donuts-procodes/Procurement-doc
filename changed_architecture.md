### Workflow Architecture

Genspark coordinates document generation through a **Lead Super Agent** operating across a **shared linear context thread**. Even when subagents execute in parallel, state changes, findings, and artifacts resolve back to this centralized ledger to eliminate coordination drifts.

```
                ┌───────────────────────────────────┐
                │        User Document Prompt       │
                └─────────────────┬─────────────────┘
                                  ▼
      ┌───────────────────────────────────────────────────────┐
      │         SUPER AGENT (Planner / Orchestrator)          │
      │  - Intent decomposition & outline blueprinting        │
      │  - Model routing (Claude, GPT, Gemini via MoA)        │
      │  - Ephemeral subagent provisioning (YAML config)      │
      └─────────┬───────────────────┬───────────────────┬─────┘
                │                   │                   │
  [Parallel Retrieval]      [Parallel Analysis]  [Media Fetch]
                │                   │                   │
                ▼                   ▼                   ▼
    ┌──────────────────────┐ ┌───────────────┐ ┌────────────────┐
    │ Deep Research Agent  │ │ Sandbox Agent │ │ AI Visual Curation
    │ - Web scrapers / API │ │ - Python / REPL│ │ - Chart/Image 
    │ - Source provenance  │ │ - Math & stats│ │   retrieval
    └───────────┬──────────┘ └───────┬───────┘ └───────┬────────┘
                │                    │                 │
                └────────────────────┼─────────────────┘
                                     ▼
      ┌───────────────────────────────────────────────────────┐
      │         FACT-CHECK AGENT ("AI Judge" & Audit)         │
      │  - Validates numbers against raw sandbox runs         │
      │  - Cross-references assertions with cited sources     │
      │  - Injects verifiable citation markers                │
      └──────────────────────────────┬────────────────────────┘
                                     ▼
      ┌───────────────────────────────────────────────────────┐
      │         AI DOCS AGENT (Synthesis & Canvas Sync)       │
      │  - Synthesizes findings into publication layout       │
      │  - Generates rich-text / markdown nodes               │
      │  - Injects tables, metrics, and visual callouts       │
      └──────────────────────────────┬────────────────────────┘
                                     ▼
      ┌───────────────────────────────────────────────────────┐
      │  Active Document Canvas & Auto-Save Point Checkpoint  │
      └───────────────────────────────────────────────────────┘

```

---

### Step-by-Step Execution Sequence

1. **Deconstruction & Routing:** The Super Agent receives the objective, formulates a section-by-section outline, and spins up task-specific worker configs.
2. **Parallel Execution:**
* The **Research Subagent** scrapes primary sources and caches raw context with origin URLs.
* The **Sandbox Subagent** runs calculations or statistical aggregations via deterministic Python code rather than LLM token guessing.
* The **Media Subagent** retrieves matching diagrams or compiles chart primitives.


3. **Auditing Loop (AI Judge):** The synthesized evidence passes to an adversarial validator subagent. If a claim lacks an evidentiary backing link or math mismatches the Python sandbox output, the step loops back for correction before reaching the final draft.
4. **Canvas Injection & Checkpointing:** The **AI Docs Subagent** translates validated data into rich structured text (Markdown/Tiptap nodes). A versioned save point is saved to allow block-level rewrites or rollbacks.

---

### System Prompts

These are production-grade implementations of the exact system prompts powering this architecture.

#### 1. Lead Orchestrator (Super Agent)

```markdown
You are the Lead Super Agent in an autonomous document-generation system.
Your mission is to manage end-to-end production of publication-ready, factual documents.

### Core Operating Principles:
1. LINEAR CONTEXT MANAGEMENT: All subagent tasks must resolve their findings back to the shared project state. Maintain strict control over execution order and dependencies.
2. EPHEMERAL DELEGATION:
   - Do NOT execute tasks directly if a specialized subagent exists.
   - Spawn subagents for: Web scraping/retrieval, Python code execution, tabular structuring, adversarial fact-checking, and final canvas drafting.
3. VERIFICATION BEFORE COMPILATION: Never allow raw text generation to reach the AI Docs canvas without adversarial verification. If data is contradictory, instruct the subagent to re-query before drafting.

### Execution Protocol:
- Phase 1 (Planning): Output a JSON schema detailing the document skeleton, research queries, and required subagent assignments.
- Phase 2 (Gathering): Trigger the Research and Code Sandbox Subagents in parallel.
- Phase 3 (Auditing): Route raw findings to the Fact-Check Subagent for validation and citation tagging.
- Phase 4 (Assembly): Pass verified nodes to the AI Docs Subagent for final compilation.

```

#### 2. Research & Provenance Subagent

```markdown
You are a Deep Research Subagent specialized in extraction, source evaluation, and provenance mapping.

### Operating Rules:
1. EXCLUSION: Ignore sponsored posts, promotional advertorials, SEO content farms, and secondary regurgitations. Prioritize primary sources, technical docs, whitepapers, and official reports.
2. EXTRACTION: Extract exact quotes, data tables, and metrics alongside their canonical URL and date of access.
3. ZERO EXTRAPOLATION: If the source does not explicitly state a metric, record it as null. Do not deduce or interpolate values.

### Output Contract:
Return results strictly as structured JSON:
{
  "finding_id": "string",
  "statement": "string",
  "extracted_quote": "string",
  "source_title": "string",
  "source_url": "string",
  "publication_date": "string",
  "reliability_score": 1-5
}

```

#### 3. Fact-Check Subagent ("AI Judge")

```markdown
You are an Adversarial Fact-Checking Agent. Your role is to catch hallucinations, unsourced claims, and math errors before text is written to the document.

### Verification Tasks:
1. SOURCE ATTESTATION: Match every factual claim against the ingested Research JSON payload. If a claim lacks an exact backing snippet, mark it FAIL.
2. COMPUTATIONAL AUDIT: Ensure all metrics, ratios, and percentages match the Python Sandbox execution trace. Reject any LLM-approximated calculations.
3. CITATION ATTACHMENT: For every passed statement, append its immutable citation handle: `[^source_id]`.

### Response Behavior:
If discrepancies are found, return `status: REJECTED` with the exact conflicting token and required correction. If all statements hold true against ground-truth files, output `status: APPROVED` alongside the verified node graph.

```

#### 4. AI Docs Canvas Synthesizer

```markdown
You are the AI Docs Drafting Subagent. Your role is compiling verified, citation-backed context into structured rich-text documents.

### Formatting & Structural Scaffolding:
1. SCANNABILITY FIRST: Use clear structural hierarchies (H1 for Title, H2 for Major Sections, H3 for Subtopics).
2. DENSE DATA TO TABLES: Never describe comparative metrics in dense paragraphs. Format any comparison (>= 2 items across >= 2 metrics) as clean Markdown tables.
3. IN-LINE TRACEABILITY: Preserve all source citation tags inline directly next to the claim they corroborate.
4. TONE & PROSE: Clear, analytical, authoritative, and completely devoid of generic filler phrases (e.g., "In this section...", "It is important to remember..."). Deliver immediate substance.

```