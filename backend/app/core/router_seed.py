"""Database schema metadata for semantic routing.

This module defines the structural metadata for all target databases and
indexes that can be queried via the RAG system. These schemas are seeded
into Qdrant on application startup and used for semantic routing.
"""

from langchain_core.documents import Document


def get_schema_documents() -> list[Document]:
    """
    Returns a list of LangChain Documents describing the target databases
    and their schemas. These are ingested into Qdrant for semantic routing.
    """

    documents = [
        # PostgreSQL: Incidents and Case Management
        Document(
            page_content=(
                "PostgreSQL Incident Management Database. "
                "Contains structured incident records, case tickets, and SOC analyst notes. "
                "Use this database for historical incident queries, trend analysis, case lookups, "
                "and analyst feedback. "
                "Key entities: incidents, playbooks, users, feedback, case_assignments. "
                "Common queries: 'Show me all critical incidents from last week', "
                "'What playbook was used for incident 123', "
                "'How many cases did analyst Alice close this month'."
            ),
            metadata={
                "target_db": "postgresql",
                "query_syntax": "SQL",
                "database": "soar_db",
                "connection_string": "postgresql://postgres:postgres@db:5432/soar_db",
                "tables": [
                    {
                        "name": "incidents",
                        "description": "Incident records with severity, status, timestamps",
                        "key_columns": ["id", "severity", "status", "created_at", "description", "source"],
                    },
                    {
                        "name": "playbooks",
                        "description": "Automated response playbooks and their execution history",
                        "key_columns": ["id", "name", "action", "trigger_type", "execution_count"],
                    },
                    {
                        "name": "users",
                        "description": "SOC analyst user accounts and roles",
                        "key_columns": ["id", "username", "email", "role", "active"],
                    },
                    {
                        "name": "case_assignments",
                        "description": "Links incidents to assigned analysts and cases",
                        "key_columns": ["id", "incident_id", "assigned_to", "case_id", "assignment_date"],
                    },
                    {
                        "name": "feedback",
                        "description": "Analyst feedback on model predictions and false positives",
                        "key_columns": ["id", "incident_id", "feedback_type", "verdict", "analyst_id", "timestamp"],
                    },
                ],
                "use_cases": [
                    "incident_history",
                    "case_management",
                    "playbook_performance",
                    "analyst_metrics",
                    "feedback_trends",
                ],
            },
        ),
        # OpenSearch: Network Detection Logs
        Document(
            page_content=(
                "OpenSearch Network Detection Indices. "
                "Contains real-time and historical network detection logs from Suricata IDS, Zeek monitoring, "
                "and Wazuh alerts. Use this for network behavior analysis, threat hunting, IoC lookups, "
                "and real-time security event correlation. "
                "Key indices: suricata-logs, zeek-logs, wazuh-alerts. "
                "Common queries: 'Show me all IPS alerts on host 192.168.1.100', "
                "'What are the top destination IPs contacted today', "
                "'Find DNS tunneling activity in the last hour'."
            ),
            metadata={
                "target_db": "opensearch",
                "query_syntax": "OpenSearch Query DSL (JSON)",
                "host": "opensearch",
                "port": 9200,
                "username": "admin",
                "indices": [
                    {
                        "name": "suricata-logs-*",
                        "description": "IDS/IPS alerts and packet analysis from Suricata",
                        "key_fields": [
                            "src_ip",
                            "dest_ip",
                            "src_port",
                            "dest_port",
                            "protocol",
                            "alert.signature",
                            "alert.severity",
                            "timestamp",
                        ],
                    },
                    {
                        "name": "zeek-logs-*",
                        "description": "Network metadata and DNS/HTTP/SSL logs from Zeek",
                        "key_fields": [
                            "src_ip",
                            "dest_ip",
                            "event_type",
                            "protocol",
                            "query",
                            "uri",
                            "timestamp",
                        ],
                    },
                    {
                        "name": "wazuh-alerts-*",
                        "description": "SIEM alerts, policy violations, and threat intel matches from Wazuh",
                        "key_fields": [
                            "source",
                            "rule_id",
                            "rule_name",
                            "severity",
                            "agent_id",
                            "hostname",
                            "timestamp",
                        ],
                    },
                ],
                "use_cases": [
                    "network_threat_hunting",
                    "ioc_lookup",
                    "lateral_movement_detection",
                    "dns_analysis",
                    "real_time_alerting",
                ],
            },
        ),
        # PostgreSQL: Threat Intelligence and Enrichment
        Document(
            page_content=(
                "PostgreSQL Threat Intelligence Cache. "
                "Stores cached threat intelligence lookups, IOC enrichment data, and external API responses. "
                "Use this for fast IOC validation, historical threat data queries, and enrichment statistics. "
                "Key entities: threat_intel_cache, iocs, ip_reputation, domain_reputation. "
                "Common queries: 'Has IP 8.8.8.8 been seen as malicious', "
                "'Show me all IOCs from the last 7 days', "
                "'What's the reputation score for domain evil.com'."
            ),
            metadata={
                "target_db": "postgresql",
                "query_syntax": "SQL",
                "database": "soar_db",
                "connection_string": "postgresql://postgres:postgres@db:5432/soar_db",
                "tables": [
                    {
                        "name": "threat_intel_cache",
                        "description": "Cached external threat intelligence responses",
                        "key_columns": ["id", "indicator", "source", "threat_level", "cached_at"],
                    },
                    {
                        "name": "iocs",
                        "description": "Indicators of Compromise",
                        "key_columns": ["id", "ioc_value", "ioc_type", "severity", "source"],
                    },
                ],
                "use_cases": [
                    "ioc_lookup",
                    "reputation_queries",
                    "enrichment_cache_hit_rate",
                ],
            },
        ),
    ]

    return documents


async def seed_qdrant(vector_store) -> None:
    """Seed Qdrant with schema documents if the collection is empty."""
    documents = get_schema_documents()
    
    # Add documents to vector store with metadata
    # The vector_store.add_documents() method will handle chunking and embedding
    try:
        vector_store.add_documents(documents, ids=[doc.metadata.get("target_db", "unknown") for doc in documents])
    except Exception as e:
        # If docs already exist, silently continue
        pass
