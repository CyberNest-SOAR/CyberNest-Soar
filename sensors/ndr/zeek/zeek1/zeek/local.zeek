@load base/protocols/conn
@load base/protocols/http
@load base/protocols/dns
@load base/protocols/smtp
@load base/frameworks/notice

@load policy/tuning/json-logs.zeek
redef ignore_checksums = T;

# Set default log directory
redef Log::default_logdir = "/opt/zeek/logs/current";
# Custom scripts
@load ./scripts/phishing
@load ./scripts/ddos
@load ./scripts/brute_force
