/**
 * Safe, robust parser for NDJSON datasets using ReadableStream.
 * Handles split-line boundaries across chunks, individual parsing failures, and schema mapping.
 */

export interface NormalizedHostContext {
  hostname: string;
  ip_address: string;
  mac_address: string | null;
  os_name: string | null;
}

export interface NormalizedEnrichmentData {
  risk_score: number;
  vt_score: number;
  abuse_score: number;
  epss_score: number | null;
  cvss_score: number | null;
  misp_matches: string[];
  tags: string[];
  debug_info: Record<string, any>;
}

export interface NormalizedAlert {
  event_id: string;
  source: string;
  timestamp: string;
  description: string;
  severity: number;
  host_context: NormalizedHostContext;
  enrichment_data: NormalizedEnrichmentData;
  confidence: number | string;
  raw_data?: any;
}

/**
 * Normalizes an alert object from the new NDJSON schema to match the original wazuh_alerts schema
 * while ensuring safe checks for undefined or missing fields.
 */
export function normalizeAlert(raw: any): NormalizedAlert {
  if (!raw) {
    return {
      event_id: "unknown",
      source: "unknown",
      timestamp: new Date().toISOString(),
      description: "No description available",
      severity: 0,
      host_context: { hostname: "Unknown", ip_address: "N/A", mac_address: null, os_name: null },
      enrichment_data: { risk_score: 0, vt_score: 0, abuse_score: 0, epss_score: null, cvss_score: null, misp_matches: [], tags: [], debug_info: {} },
      confidence: "-"
    };
  }

  // 1. Map Severity (alert_severity in NDJSON, severity in old Wazuh JSON)
  const severity = raw.alert_severity !== undefined ? Number(raw.alert_severity) : (raw.severity !== undefined ? Number(raw.severity) : 0);

  // 2. Map Host Context
  const hostname = raw.host_role || raw.src_user || raw.host_context?.hostname || "Unknown Host";
  const ip_address = raw.src_ip || raw.host_context?.ip_address || "N/A";
  const mac_address = raw.host_context?.mac_address || null;
  const os_name = raw.process_name || raw.host_context?.os_name || null;

  // 3. Map Enrichment Data
  // In NDJSON, risk_adjusted_priority acts as the risk score. We default to a scaled value or 0.
  const risk_score = raw.risk_adjusted_priority !== undefined ? Number(raw.risk_adjusted_priority) : (raw.enrichment_data?.risk_score !== undefined ? Number(raw.enrichment_data.risk_score) : 0);
  const vt_score = raw.enrichment_vt_score !== undefined ? Number(raw.enrichment_vt_score) : (raw.enrichment_data?.vt_score !== undefined ? Number(raw.enrichment_data.vt_score) : 0);
  const abuse_score = raw.enrichment_abuse_score !== undefined ? Number(raw.enrichment_abuse_score) : (raw.enrichment_data?.abuse_score !== undefined ? Number(raw.enrichment_data.abuse_score) : 0);
  const epss_score = raw.enrichment_epss_score !== undefined && raw.enrichment_epss_score !== null ? Number(raw.enrichment_epss_score) : (raw.enrichment_data?.epss_score !== undefined ? raw.enrichment_data.epss_score : null);
  const cvss_score = raw.enrichment_cvss_score !== undefined && raw.enrichment_cvss_score !== null ? Number(raw.enrichment_cvss_score) : (raw.enrichment_data?.cvss_score !== undefined ? raw.enrichment_data.cvss_score : null);
  const misp_matches = raw.enrichment_misp_matches || raw.enrichment_data?.misp_matches || [];
  const tags = raw.tags || raw.enrichment_data?.tags || [];
  const debug_info = raw.debug_info || raw.enrichment_data?.debug_info || {};

  // 4. Map Confidence
  const confidence = raw.confidence !== undefined ? raw.confidence : "-";

  // 5. Map Source (dataset_source in NDJSON, source in old schema)
  const sourceRaw = raw.dataset_source || raw.source || "Unknown";
  // Clean up source prefixes for cleaner visual rendering
  const source = sourceRaw.startsWith("synthetic.") ? sourceRaw.substring(10) : sourceRaw;

  // 6. Map Description (alert_signature in NDJSON, description in old schema)
  const description = raw.alert_signature || raw.description || `${raw.event_type || 'Event'} detected`;

  return {
    ...raw, // keep raw fields for full JSON inspection drawer
    event_id: raw.event_id || `evt-${Math.random().toString(36).substring(2, 9)}`,
    source,
    timestamp: raw.timestamp || new Date().toISOString(),
    description,
    severity,
    host_context: {
      hostname,
      ip_address,
      mac_address,
      os_name
    },
    enrichment_data: {
      risk_score,
      vt_score,
      abuse_score,
      epss_score,
      cvss_score,
      misp_matches,
      tags,
      debug_info
    },
    confidence
  };
}

/**
 * Streams, parses, and normalizes a remote/local NDJSON file using browser streams.
 * Handles split lines across chunks and isolates malformed lines gracefully.
 * 
 * @param url The asset or static path of the NDJSON file.
 * @param maxItems The threshold capping array objects in RAM.
 * @returns Array of normalized objects.
 */
export async function parseNDJSONStream(url: string, maxItems: number = 5000): Promise<NormalizedAlert[]> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`HTTP network error: status ${response.status} ${response.statusText}`);
  }
  if (!response.body) {
    throw new Error("Invalid stream response body from dataset.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  
  let buffer = "";
  const items: NormalizedAlert[] = [];
  
  try {
    while (true) {
      const { value: chunk, done: readerDone } = await reader.read();
      
      if (chunk) {
        // Decode chunk and append to current split buffer
        buffer += decoder.decode(chunk, { stream: !readerDone });
        const lines = buffer.split("\n");
        
        // Pop off the last element which might be split across the chunk boundary
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed) {
            try {
              const rawObj = JSON.parse(trimmed);
              items.push(normalizeAlert(rawObj));
              
              if (items.length >= maxItems) {
                // Cancel reading from the HTTP stream early to save user bandwidth & browser RAM
                await reader.cancel("Reached maximum parsing threshold.");
                return items;
              }
            } catch (err) {
              // Safe error handling for malformed JSON lines to avoid dashboard crashes
              console.warn("Skipping malformed NDJSON line parsing error:", err, trimmed.substring(0, 100));
            }
          }
        }
      }
      
      if (readerDone) {
        break;
      }
    }
    
    // Parse any remaining line cut off at the end of the file
    if (buffer.trim()) {
      try {
        const rawObj = JSON.parse(buffer.trim());
        items.push(normalizeAlert(rawObj));
      } catch (err) {
        console.warn("Skipping malformed terminal NDJSON line parsing error:", err, buffer.trim().substring(0, 100));
      }
    }
  } catch (streamErr) {
    console.error("Stream reader encountered an execution failure:", streamErr);
    // If we've already loaded some items, return them as fallback instead of crashing completely
    if (items.length > 0) {
      return items;
    }
    throw streamErr;
  } finally {
    reader.releaseLock();
  }
  
  return items;
}
