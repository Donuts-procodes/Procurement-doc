import base64
import logging

logger = logging.getLogger(__name__)


async def kms_decrypt(ciphertext_blob: str, region_name: str = "us-east-1") -> str:
    """Decrypts KMS-encrypted LLM API keys in memory only."""
    if not ciphertext_blob:
        return ""
    try:
        import boto3
        client = boto3.client("kms", region_name=region_name or "us-east-1")
        raw_bytes = base64.b64decode(ciphertext_blob)
        response = client.decrypt(CiphertextBlob=raw_bytes)
        plaintext: bytes = response["Plaintext"]
        return plaintext.decode("utf-8")
    except Exception as exc:
        logger.warning(f"KMS Decryption failed or running in local dev mode: {exc}")
        # Return as-is if plain key was provided during development/testing
        return ciphertext_blob

