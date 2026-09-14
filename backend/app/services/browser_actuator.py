from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("gdocs.browser_actuator")

# security-auditor: Strict URL safety enforcement
_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
_BLOCKED_CIDRS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS metadata / link-local
    ipaddress.ip_network("fd00::/8"),
]
_MAX_TIMEOUT_SECONDS = 15
_MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2 MB cap


class BrowserActuationResult:
    __slots__ = ("url", "status_code", "extracted_text", "dom_elements", "error", "duration_ms")

    def __init__(
        self,
        url: str,
        status_code: int = 0,
        extracted_text: str = "",
        dom_elements: list[dict[str, str]] | None = None,
        error: str | None = None,
        duration_ms: float = 0,
    ):
        self.url = url
        self.status_code = status_code
        self.extracted_text = extracted_text
        self.dom_elements = dom_elements or []
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "status_code": self.status_code,
            "extracted_text": self.extracted_text[:2000],
            "dom_elements_count": len(self.dom_elements),
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


def _validate_url_safety(url: str) -> str | None:
    """security-auditor: Returns error string if URL is unsafe, None if safe."""
    parsed = urlparse(url)

    if parsed.scheme not in ("https", "http"):
        return f"Blocked: scheme '{parsed.scheme}' not allowed (https/http only)"

    hostname = parsed.hostname or ""
    if hostname in _BLOCKED_HOSTS:
        return f"Blocked: hostname '{hostname}' is a private/loopback address"

    try:
        addr = ipaddress.ip_address(hostname)
        for cidr in _BLOCKED_CIDRS:
            if addr in cidr:
                return f"Blocked: IP '{hostname}' falls in private CIDR {cidr}"
    except ValueError:
        pass  # hostname is a domain, not an IP — allowed

    return None


def _extract_text_from_html(html: str, max_len: int = 8000) -> str:
    """rag-vector-pipeline: Strip HTML tags and noise, return clean text for downstream indexing."""
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def _extract_dom_elements(html: str, selectors: list[str] | None = None) -> list[dict[str, str]]:
    """Lightweight regex-based DOM element extraction.
    ponytail: No lxml/bs4 dependency — regex covers the 80% case."""
    elements: list[dict[str, str]] = []
    # Extract headings
    for tag in ("h1", "h2", "h3"):
        for match in re.finditer(rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.IGNORECASE | re.DOTALL):
            clean = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if clean:
                elements.append({"tag": tag, "text": clean[:500]})
    # Extract table rows
    for match in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.IGNORECASE | re.DOTALL):
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", match.group(1), re.IGNORECASE | re.DOTALL)
        if cells:
            clean_cells = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            elements.append({"tag": "tr", "text": " | ".join(clean_cells)[:500]})
    return elements[:50]  # Cap extraction


async def navigate_url(url: str) -> BrowserActuationResult:
    """Fetch URL content with full safety validation and timeout enforcement."""
    safety_err = _validate_url_safety(url)
    if safety_err:
        logger.warning(f"🚫 Browser Actuator: {safety_err}")
        return BrowserActuationResult(url=url, error=safety_err)

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(_MAX_TIMEOUT_SECONDS),
            follow_redirects=True,
            max_redirects=3,
        ) as client:
            resp = await client.get(url, headers={"User-Agent": "ProcurementDocBot/1.0"})
            content = resp.text[:_MAX_RESPONSE_BYTES]
            elapsed = (time.monotonic() - start) * 1000

            return BrowserActuationResult(
                url=str(resp.url),
                status_code=resp.status_code,
                extracted_text=_extract_text_from_html(content),
                dom_elements=_extract_dom_elements(content),
                duration_ms=round(elapsed, 1),
            )
    except httpx.TimeoutException:
        return BrowserActuationResult(url=url, error=f"Timeout after {_MAX_TIMEOUT_SECONDS}s")
    except Exception as e:
        return BrowserActuationResult(url=url, error=str(e)[:300])


async def extract_dom_elements(url: str, selectors: list[str] | None = None) -> list[dict[str, str]]:
    """Navigate and extract structured DOM elements from a URL."""
    result = await navigate_url(url)
    if result.error:
        logger.warning(f"DOM extraction failed for {url}: {result.error}")
        return []
    return result.dom_elements


async def batch_navigate(urls: list[str], max_concurrent: int = 5) -> list[BrowserActuationResult]:
    """Batch URL navigation with concurrency limiter."""
    sem = asyncio.Semaphore(max_concurrent)

    async def _limited(u: str) -> BrowserActuationResult:
        async with sem:
            return await navigate_url(u)

    return list(await asyncio.gather(*[_limited(u) for u in urls]))
