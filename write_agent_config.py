import json

target_file = r"C:\Users\DELL\work\bigzbyagent\voicelatex-agents\apps\procurement-service\agent_config.json"

manifest = {
  "id": "agent-procurement-service-001",
  "name": "Enterprise Procurement Generator",
  "setupMode": "self-service",
  "template": {
    "id": "procurement-template-001",
    "name": "Procurement Graph AI",
    "slug": "enterprise-procurement-generator",
    "description": "Automate drafting of highly structured enterprise procurement documents (RFPs, RFQs, SOWs). Handles context retrieval, table generation, and compliance checks via parallel LangGraph nodes.",
    "shortDesc": "Automated drafting of RFI, RFP, and SOW documents",
    "tags": [
      "Procurement",
      "Document Generation",
      "RAG",
      "Enterprise Compliance"
    ],
    "systemPrompt": "You are the {agentName}, an enterprise procurement assistant.\n\nROLE\nYou help organizations draft, format, and stylize formal procurement documents. You have access to a vector database containing corporate guidelines, previous proposals, and vendor specs. Your goal is to draft comprehensive, legally compliant documents based on the user's brief.\n\nINSTRUCTIONS\n1. Classify Document: RFP, RFQ, RFI, SOW, etc.\n2. Information Extraction: Extract missing metadata (Budget, Deadline, Vendor).\n3. Retrieve Context: Query Vector DB for boilerplate clauses.\n4. Draft Segments: Compose structured TipTap JSON segments concurrently.\n5. Verify: Audit drafted content for unresolved placeholders.",
    "isActive": True,
    "createdAt": "2026-08-27T12:00:00.000Z",
    "updatedAt": "2026-08-27T12:00:00.000Z"
  },
  "voiceConfig": {
    "id": "procurement-voice-001",
    "isEnabled": False,
    "isFallbackToText": True,
    "agentId": "agent-procurement-service-001"
  },
  "guardrail": {
    "id": "procurement-guardrail-001",
    "blockedWords": ["placeholder", "draft"],
    "avoidRules": [
      "Do not invent legal clauses that contradict the uploaded corporate Knowledge Base.",
      "Do not leave bracketed placeholders like [Vendor Name] in the final output.",
      "Do not generate consumer privacy policies instead of enterprise software terms."
    ],
    "businessRules": "All intellectual property rights must default to 'work-made-for-hire' unless overridden by context.",
    "humanHandoffEnabled": False,
    "conversationMemory": True,
    "conversationLogging": True,
    "agentId": "agent-procurement-service-001"
  },
  "knowledgeSources": [
    {
      "id": "ks-procurement-chroma-001",
      "type": "database",
      "name": "Procurement RAG Vector Database",
      "isIndexed": True,
      "urlProvider": "chromadb",
      "agentId": "agent-procurement-service-001"
    }
  ],
  "agents": [
    {
      "id": "doc_type_classifier",
      "name": "Document Type Classifier",
      "systemPrompt": "Classify the following user prompt into exactly one of these procurement document types: \nRFP, RFQ, RFI, PURCHASE_ORDER, VENDOR_CONTRACT, SOW, VENDOR_SCORECARD.\n\nPrompt: {state.raw_prompt}"
    },
    {
      "id": "fillup_agent",
      "name": "Information Extraction Agent (Batched)",
      "systemPrompt": "Determine if details for '{field_human}' are present in the user prompt, uploaded document context, OR previous session chat history.\n\nUser Prompt:\n{state.raw_prompt}\n\nSession Chat History:\n{session_history}\n\nUploaded Knowledge Base Context:\n{kb_text if kb_text else 'None'}\n\nReturn extracted=True if present or inferable, plus a concise summary."
    },
    {
      "id": "segment_generation",
      "name": "Segment Generation Agent (Parallel)",
      "systemPrompt": "Draft section '{sec.title}' for an enterprise procurement {doc_type.value}.\nGuidance: {sec.guidance}\n\nCRITICAL RULES:\n2. ADHERE TO TEMPLATE GUIDANCE: Strictly follow the structure, tone, and logic specified for this template. Do not hallucinate unrelated features.\n3. HIERARCHICAL HEADINGS (H2, H3): Structure paragraphs with clear sub-headings using '## ' for H2 sub-sections and '### ' for H3 subsection details.\n4. FULL PAGE DENSITY (NO HALF-EMPTY PAGES): Write comprehensive, in-depth technical & legal prose (3 to 5 rich paragraphs per section) with bullet points and structured evaluation tables so every page card is fully filled from top to bottom.\n5. FORMATTED BULLETS & TABLES: Provide structured bullet lists for deliverables and requirements, and tables for timelines, budgets, and compliance metrics.\n6. INJECT IMAGES ANYWHERE: To insert an available image anywhere within the document text, return the exact tag [IMAGE: <image_id>] as a standalone paragraph.\nAvailable images:\n{extracted_images_list}\n\nCombined Context:\n{combined_context}\n\nKnowledge Base Context:\n{context_block}"
    },
    {
      "id": "verifier_agent",
      "name": "Quality Assurance Verifier (Parallel)",
      "systemPrompt": "Review this TipTap JSON document segment for the following issues:\n1. Unresolved bracketed placeholders (e.g., [Insert Date], [Vendor Name]). Replace them with realistic inferred values.\n2. Broken or malformed [IMAGE: xxx] tags.\n3. Empty or malformed table cells.\nIf issues exist, set is_valid to false and provide the FULL, CORRECTED JSON string in fixed_json_string.\nIf no issues, set is_valid to true.\n\nSegment JSON:\n{content_str}"
    }
  ],
  "backendFunctions": [
    {
      "name": "chroma_dense_search",
      "module": "src.services.vector_store.KnowledgeBase.query",
      "description": "Executes dense similarity searches against the ChromaDB vector collections to retrieve highly relevant corporate context chunks."
    },
    {
      "name": "pdf_asset_extraction",
      "module": "src.services.document_parser.extract_images_from_pdf",
      "description": "Scrapes embedded diagrams, logos, and high-fidelity visual assets from user-uploaded PDFs, converting them directly to Base64 for agent insertion."
    },
    {
      "name": "table_math_compiler",
      "module": "src.services.structured_tables.compute_line_items",
      "description": "Performs deterministic mathematical validations on LLM-generated line items, calculating subtotals, tax rates, and grand totals to prevent AI math hallucinations."
    },
    {
      "name": "tiptap_canvas_compiler",
      "module": "src.services.tiptap_engine.build_tiptap_segment_doc",
      "description": "Translates unstructured LLM prose into highly rigid TipTap JSON structures so the React frontend can render it beautifully as an interactive rich-text document."
    }
  ],
  "environmentVariables": [
    {
      "name": "OPENAI_API_KEY",
      "required": True,
      "description": "Required for the core GPT-4o LLM nodes in the LangGraph workflow."
    },
    {
      "name": "ANTHROPIC_API_KEY",
      "required": False,
      "description": "Optional fallback provider for Claude models."
    },
    {
      "name": "CORS_ORIGINS",
      "required": False,
      "default": "http://localhost:5173",
      "description": "Allowed origins to accept requests from the React frontend."
    }
  ],
  "llmConfigurations": [
    {
      "provider": "openai",
      "model": "gpt-4o",
      "defaultTemperature": 0.2,
      "roles": ["classifier", "extractor", "generator", "verifier"]
    }
  ],
  "apiEndpoints": [
    {
      "path": "/api/v1/generate",
      "method": "POST",
      "description": "Triggers the main LangGraph agent workflow."
    },
    {
      "path": "/api/v1/knowledge/upload",
      "method": "POST",
      "description": "Uploads, extracts, chunks, and stores PDFs/DOCX files into ChromaDB."
    },
    {
      "path": "/api/v1/session",
      "method": "POST",
      "description": "Initializes a new procurement generation session."
    }
  ],
  "vectorDatabase": "chromadb",
  "chromaDatabasePath": "./chroma_data",
  "chromaCollectionFormat": "kb_{collection_type}_{kb_id}"
}

with open(target_file, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("Successfully wrote agent_config.json")
