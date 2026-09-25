"""Domains W7 may fetch from, with their usual licence. The Institution must approve this list.

This starting list comes from TECH_STACK.md section 7. Change it only through a reviewed PR.
"""

from urllib.parse import urlparse

ALLOWED_DOMAINS: dict[str, str] = {
    "openstax.org": "CC BY 4.0",
    "libretexts.org": "CC BY NC SA",
    "medlineplus.gov": "public domain",
    "ncbi.nlm.nih.gov": "per article",
    "europepmc.org": "per article",
    "cdc.gov": "public domain",
}


def is_allowed(url: str) -> bool:
    """True when the host is an allowed domain or one of its subdomains."""
    host = (urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS)
