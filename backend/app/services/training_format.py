"""
services/training_format.py — Converts live Wazuh alerts into the
dataset_pipeline UnifiedAlert training format so AI models see the
same 100+ field schema during inference as they were trained on.

Usage:
    from services.training_format import to_training_format

    alert = to_training_format(opensearch_hit)   # single
    alerts = batch_to_training_format(hits)       # batch
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Find project root (look for a sentinel like .git or dataset_pipeline)
_PROJECT_ROOT = Path(__file__).resolve()
for _ in range(10):
    if (_PROJECT_ROOT / "dataset_pipeline").is_dir():
        break
    _PROJECT_ROOT = _PROJECT_ROOT.parent
_dataset_pipeline_dir = str(_PROJECT_ROOT / "dataset_pipeline")
if _dataset_pipeline_dir not in sys.path:
    sys.path.insert(0, _dataset_pipeline_dir)

from parsers.wazuh_mapper import (  # noqa: E402
    wazuh_to_unified_alert,
    apply_enrichment_flat,
    batch_map_wazuh_hits,
)


def to_training_format(
    hit: Dict[str, Any],
    enrichment_data: Any = None,
) -> Dict[str, Any]:
    """
    Convert a single OpenSearch hit into the training-format UnifiedAlert dict.
    Output includes ALL schema fields (even null) so AI models see the same
    100+ field schema during inference as during training.
    """
    source = hit.get("_source", hit)
    alert = wazuh_to_unified_alert(source)
    if enrichment_data is not None:
        apply_enrichment_flat(alert, enrichment_data)
    return _to_complete_dict(alert)


def batch_to_training_format(
    hits: List[Dict[str, Any]],
    enrichment_results: List[Any] = None,
) -> List[Dict[str, Any]]:
    """
    Convert multiple OpenSearch hits into training-format dicts.
    """
    alerts = batch_map_wazuh_hits(hits)
    if enrichment_results:
        for alert, enrichment in zip(alerts, enrichment_results):
            if enrichment is not None and not isinstance(enrichment, Exception):
                try:
                    apply_enrichment_flat(alert, enrichment)
                except Exception as e:
                    logger.warning("Enrichment flat-map failed for %s: %s", alert.event_id, e)
    return [_to_complete_dict(a) for a in alerts]


def _to_complete_dict(alert) -> Dict[str, Any]:
    """
    Serialize UnifiedAlert to a dict with ALL schema fields present,
    including nulls — so the AI model always sees the full schema.
    """
    import datetime
    from dataclasses import fields

    d = {}
    for f in fields(alert):
        v = getattr(alert, f.name)
        if isinstance(v, datetime.datetime):
            d[f.name] = v.isoformat()
        elif isinstance(v, set):
            d[f.name] = list(v)
        elif isinstance(v, dict):
            d[f.name] = dict(v) if v else {}
        else:
            d[f.name] = v
    return d
