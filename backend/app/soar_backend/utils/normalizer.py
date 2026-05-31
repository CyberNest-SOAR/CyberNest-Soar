def normalize_wazuh(alert):
    src = alert["_source"]
    return {
        "event_id": alert["_id"],
        "timestamp": src["@timestamp"],
        "host": src.get("agent", {}),
        "severity": src["rule"]["level"]
    }

## Less Complex alert structure

#def normalize_wazuh(alert):
#    src = alert["_source"]
#
#    return {
#        "event_id": alert["_id"],
#        "timestamp": src["@timestamp"],
#        "host": {
#            "name": src.get("agent", {}).get("name"),
#            "ip": src.get("agent", {}).get("ip")
#        },
#        "rule": {
#            "id": src["rule"]["id"],
#            "description": src["rule"]["description"],
#            "severity": src["rule"]["level"]
#        },
#        "ioc": {
#            "ip": src.get("srcip"),
#        }
#    }