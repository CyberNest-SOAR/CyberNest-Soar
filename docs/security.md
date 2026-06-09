# CyberNest SOAR — Security Notice

> A security platform that introduces its own vulnerabilities creates an ironic
> problem. This document describes the current security posture, known gaps,
> and hardening recommendations.

---

## Network Exposure

| Issue | Risk | Recommendation |
|-------|------|---------------|
| OpenSearch without TLS | **CRITICAL** | Enable TLS; mandatory outside isolated networks |
| No API authentication | **CRITICAL** | API key auth minimum; JWT + RBAC preferred |
| pgAdmin web exposed | **HIGH** | Never public; strong credentials + MFA |
| No network segmentation | **MEDIUM** | Restrict inter-service traffic with network policies |

## Secrets Management

Seven API keys and passwords are stored in plain-text `.env` files:

| Variable | Sensitivity |
|----------|-------------|
| `VT_API_KEY` | **CRITICAL** |
| `MISP_KEY` | **CRITICAL** |
| `ABUSEIPDB_KEY` | **HIGH** |
| `OS_USER` / `OS_PASS` | **HIGH** |

> **Recommendation:** Use HashiCorp Vault, AWS Secrets Manager, or
> Kubernetes Secrets for production. Plain-text `.env` files in version
> control are unacceptable for production deployments.

## Container Security

| Gap | Severity | Recommendation |
|-----|----------|---------------|
| No AppArmor / seccomp policies | **HIGH** | Document and apply hardening profiles |
| Root user containers | **MEDIUM** | Run with non-root user where possible |
| No persistent volume management | **HIGH** | Data loss risk on container restarts |
| No centralized backend logging | **MEDIUM** | Errors captured only in `debug_info` fields |

## API Rate Limits & Abuse

| Service | Limit | Risk | Mitigation |
|---------|-------|------|------------|
| VirusTotal | 4 req/min | **HIGH** | Redis cache (TTL 24-48h) for IP reputation |
| NVD | 6 req/sec | **LOW** | Local CVE data caching |
| AbuseIPDB | Varies | **MEDIUM** | Caching + tier upgrade |

## Playbook Safety

| Action | Risk | Mitigation |
|--------|------|------------|
| QUARANTINE_HOST | **CRITICAL** | Confirmation windows |
| BLOCK_IP | **HIGH** | Rollback capability |
| CREATE_TICKET | **LOW** | Non-disruptive |

> QUARANTINE_HOST and BLOCK_IP execute in AUTO mode for high-risk
> alerts. Without a human-in-the-loop checkpoint, a misconfigured
> enrichment pipeline can cause unnecessary service disruption.

## Operational Degradation

Under degraded conditions (external APIs unreachable), risk scores may be
significantly understated — a CRITICAL alert might score LOW if VirusTotal
is unreachable. Monitor enrichment health proactively.

The fail-soft architecture (`return_exceptions=True`, 5s timeouts) ensures
single service failures never block batch processing, but creates silent
detection degradation when MISP is unreachable.

## Licensing Risks

| Component | License | Risk |
|-----------|---------|------|
| TheHive 5 | Proprietary | **CRITICAL** — Commercial license required |
| Velociraptor | AGPLv3 | **HIGH** — Source disclosure |
| Cortex | AGPLv3 | **HIGH** — Source disclosure |
| MISP | AGPLv3 | **HIGH** — Internal deployment mitigates |
| Suricata | GPLv2 | **MEDIUM** — Copyleft; safe in SaaS |
| Wazuh | GPLv2 | **MEDIUM** — Same as Suricata |

All tools are accessed through REST APIs (sidecar/integration pattern),
not embedded code, reducing derivative work exposure under GPL/AGPL.

## Reporting Vulnerabilities

If you discover a security vulnerability in CyberNest SOAR, please report
it by opening an issue at:
https://github.com/CyberNest-SOAR/CyberNest-Soar/issues

Please include:
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential mitigations

---

**CyberNest Soar is currently under development. Monitoring all incoming
telemetry for anomalous signatures in real-time. Soon!**
