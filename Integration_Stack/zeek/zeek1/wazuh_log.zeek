module WazuhLog;

global wazuh_file: file = open("/usr/local/zeek/logs/wazuh_zeek.log");

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    print wazuh_file, fmt("{\"ts\":\"%s\",\"uid\":\"%s\",\"src_ip\":\"%s\",\"src_port\":%d,\"dest_ip\":\"%s\",\"dest_port\":%d,\"proto\":\"tcp\",\"service\":\"http\",\"method\":\"%s\",\"uri\":\"%s\"}",
        strftime("%Y-%m-%dT%H:%M:%SZ", network_time()),
        c$uid,
        c$id$orig_h,
        c$id$orig_p,
        c$id$resp_h,
        c$id$resp_p,
        method,
        original_URI);
}

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
    print wazuh_file, fmt("{\"ts\":\"%s\",\"uid\":\"%s\",\"src_ip\":\"%s\",\"src_port\":%d,\"dest_ip\":\"%s\",\"dest_port\":%d,\"proto\":\"udp\",\"service\":\"dns\",\"query\":\"%s\"}",
        strftime("%Y-%m-%dT%H:%M:%SZ", network_time()),
        c$uid,
        c$id$orig_h,
        c$id$orig_p,
        c$id$resp_h,
        c$id$resp_p,
        query);
}
