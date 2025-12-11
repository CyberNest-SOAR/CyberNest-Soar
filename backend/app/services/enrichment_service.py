
# app/services/enrichment_service.py

import re
from typing import Dict, List
from urllib.parse import urlparse

URL_RE = re.compile(r'https?://[^\s)"]+', re.IGNORECASE)
HTML_TAG_RE = re.compile(r'</?\w+[^>]*>')
DOMAIN_RE = re.compile(r'\b([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b')

SHORTENERS = {
    "bit.ly","tinyurl.com","t.co","goo.gl","ow.ly","is.gd","rebrand.ly","cutt.ly","shorturl.at"
}
SUSPICIOUS_WORDS = {
    "verify","update","urgent","account","password","login","confirm","suspend","limited","security","alert"
}

def extract_urls(text: str) -> List[str]:
    return URL_RE.findall(text or "")

def extract_domains(text: str) -> List[str]:
    domains = set()
    for u in extract_urls(text or ""):
        d = urlparse(u).netloc.lower()
        if d:
            domains.add(d)
    for m in DOMAIN_RE.finditer(text or ""):
        domains.add(m.group(1).lower())
    return sorted(domains)

def enrichment_features(subject: str, body: str) -> Dict:
    txt = f"{subject or ''}\n{body or ''}"
    txt_lower = txt.lower()

    urls = extract_urls(txt)
    domains = extract_domains(txt)
    html_tags_len = len(" ".join(HTML_TAG_RE.findall(body or "")))
    html_ratio = round(html_tags_len / max(1, len(body or "")), 3)

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
    }
