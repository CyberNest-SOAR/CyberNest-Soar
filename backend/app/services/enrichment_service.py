
# app/services/enrichment_service.py

import re
from typing import Dict, List
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s)"]+', re.IGNORECASE)
HTML_TAG_RE = re.compile(r'</?\w+[^>]*>')
DOMAIN_RE = re.compile(r'\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b')
ANCHOR_RE = re.compile(
    r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
IP_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')

SHORTENERS = {
    "bit.ly","tinyurl.com","t.co","goo.gl","ow.ly","is.gd","rebrand.ly","cutt.ly","shorturl.at"
}

SUSPICIOUS_TLDS = {
    "zip", "mov", "xyz", "top", "tk", "ml", "ga", "cf", "click", "country", "support"
}

SUSPICIOUS_WORDS = {
    "verify", "update", "urgent", "account", "password", "login", "confirm", "suspend",
    "limited", "security", "alert", "prize", "winner", "congratulations", "claim",
    "click", "act now", "immediate", "action required", "expire", "confirm identity",
    "credit card", "bank", "paypal", "amazon", "apple", "microsoft", "free", "congratulate"
}

# Brand name -> legitimate domain. Used to flag impersonation
# (brand mentioned but no link to that brand's real domain).
BRANDS = {
    "paypal": "paypal.com",
    "microsoft": "microsoft.com",
    "amazon": "amazon.com",
    "apple": "apple.com",
    "google": "google.com",
    "facebook": "facebook.com",
    "netflix": "netflix.com",
    "linkedin": "linkedin.com",
    "chase": "chase.com",
    "wells fargo": "wellsfargo.com",
    "bank of america": "bankofamerica.com",
}


def extract_urls(text: str) -> List[str]:
    return URL_RE.findall(text or "")


def extract_domains(text: str) -> List[str]:
    domains = set()
    for u in extract_urls(text or ""):
        try:
            d = urlparse(u).netloc.lower()
            if d:
                domains.add(d)
        except Exception:
            pass
    for m in DOMAIN_RE.finditer(text or ""):
        domains.add(m.group(1).lower())
    return sorted(domains)


def _safe_urlparse(u: str):
    try:
        return urlparse(u)
    except ValueError:
        # urlparse raises on malformed URLs (e.g. unbalanced brackets / bad IPv6)
        return None


def _has_ip_host(urls: List[str]) -> bool:
    for u in urls:
        parsed = _safe_urlparse(u)
        if parsed is None:
            continue
        host = parsed.hostname or ""
        if IP_RE.match(host):
            return True
    return False


def _has_punycode(domains: List[str]) -> bool:
    return any("xn--" in d for d in domains)


def _has_suspicious_tld(domains: List[str]) -> bool:
    for d in domains:
        tld = d.rsplit(".", 1)[-1] if "." in d else ""
        if tld in SUSPICIOUS_TLDS:
            return True
    return False


def _https_ratio(urls: List[str]) -> float:
    if not urls:
        return 0.0
    https = sum(1 for u in urls if u.lower().startswith("https://"))
    return round(https / len(urls), 3)


def _has_at_in_url(urls: List[str]) -> bool:
    # '@' in the authority part of a URL is a known credential-injection trick
    for u in urls:
        after_scheme = u.split("://", 1)[-1]
        if "@" in after_scheme.split("/", 1)[0]:
            return True
    return False


def _url_lex_stats(urls: List[str]) -> Dict[str, float]:
    if not urls:
        return {"avg_url_length": 0.0, "max_url_length": 0, "num_url_dots": 0, "num_url_hyphens": 0}
    lengths = [len(u) for u in urls]
    return {
        "avg_url_length": round(sum(lengths) / len(lengths), 2),
        "max_url_length": max(lengths),
        "num_url_dots": sum(u.count(".") for u in urls),
        "num_url_hyphens": sum(u.count("-") for u in urls),
    }


def _anchor_href_mismatch(body: str) -> int:
    if not body:
        return 0
    count = 0
    for href, visible in ANCHOR_RE.findall(body):
        parsed = _safe_urlparse(href)
        if parsed is None:
            continue
        href_host = parsed.netloc.lower()
        if not href_host:
            continue
        visible_domains = [m.group(1).lower() for m in DOMAIN_RE.finditer(visible)]
        if not visible_domains:
            continue
        match = any(
            vd == href_host or href_host.endswith("." + vd) or vd.endswith("." + href_host)
            for vd in visible_domains
        )
        if not match:
            count += 1
    return count


def _brand_impersonation(text_lower: str, domains: List[str]) -> bool:
    for brand, real_domain in BRANDS.items():
        if brand in text_lower:
            owns_link = any(d == real_domain or d.endswith("." + real_domain) for d in domains)
            if not owns_link:
                return True
    return False


def enrichment_features(subject: str, body: str) -> Dict:
    txt = f"{subject or ''}\n{body or ''}"
    txt_lower = txt.lower()

    urls = extract_urls(txt)
    domains = extract_domains(txt)
    html_tags_len = len(" ".join(HTML_TAG_RE.findall(body or "")))
    html_ratio = round(html_tags_len / max(1, len(body or "")), 3)
    url_stats = _url_lex_stats(urls)

    return {
        "subject_len": len(subject or ""),
        "text_len": len(txt),
        "num_urls": len(urls),
        "domains_in_text": domains,
        "has_shortener": any(d in SHORTENERS for d in domains),
        "num_exclamations": txt.count("!"),
        "num_upper_words": sum(1 for w in txt.split() if w.isupper() and len(w) >= 3),
        "num_suspicious_words": sum(1 for w in SUSPICIOUS_WORDS if w in txt_lower),
        "html_ratio": html_ratio,
        # URL lexical features
        "avg_url_length": url_stats["avg_url_length"],
        "max_url_length": url_stats["max_url_length"],
        "num_url_dots": url_stats["num_url_dots"],
        "num_url_hyphens": url_stats["num_url_hyphens"],
        "has_ip_url": _has_ip_host(urls),
        "has_punycode": _has_punycode(domains),
        "has_suspicious_tld": _has_suspicious_tld(domains),
        "https_ratio": _https_ratio(urls),
        "has_at_in_url": _has_at_in_url(urls),
        # HTML / brand features
        "anchor_href_mismatch": _anchor_href_mismatch(body or ""),
        "brand_impersonation": _brand_impersonation(txt_lower, domains),
    }
