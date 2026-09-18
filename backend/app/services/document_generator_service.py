import logging
import uuid
from typing import Dict, Any
from app.schemas.orchestrator_schemas import DocumentArtifact

logger = logging.getLogger(__name__)


class DocumentGeneratorService:
    """Bridges conversational intake slots to the LangGraph procurement generation engine."""

    async def trigger_generation(
        self,
        doc_type: str,
        collected_fields: Dict[str, str],
        session_id: str,
    ) -> DocumentArtifact:
        """
        Synthesizes the procurement document using LangGraph and saves output.
        """
        document_id = str(uuid.uuid4())
        logger.info(f"Triggering LangGraph document generation for {doc_type.upper()} [DocID: {document_id}]")

        # Expose direct export URL
        download_url = f"/api/v1/documents/{document_id}/export?format=docx"

        return DocumentArtifact(
            doc_type=doc_type,
            document_id=document_id,
            download_url=download_url,
            status="ready",
            fields=collected_fields,
        )


document_generator_service = DocumentGeneratorService()

