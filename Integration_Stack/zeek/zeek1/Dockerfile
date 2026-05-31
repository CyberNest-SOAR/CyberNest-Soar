FROM blacktop/zeek:latest

# Ensure JSON logging is enabled with a proper newline and uses ISO 8601 timestamps
RUN echo "" >> /usr/local/zeek/share/zeek/site/local.zeek && \
    echo "@load policy/tuning/json-logs.zeek" >> /usr/local/zeek/share/zeek/site/local.zeek && \
    echo "redef LogAscii::json_timestamps = JSON::TS_ISO8601;" >> /usr/local/zeek/share/zeek/site/local.zeek && \
    echo "redef ignore_checksums = T;" >> /usr/local/zeek/share/zeek/site/local.zeek

WORKDIR /usr/local/zeek/logs

# Entrypoint to run Zeek on the interface ignoring checksums (-C)
COPY wazuh_log.zeek /usr/local/zeek/share/zeek/site/wazuh_log.zeek
ENTRYPOINT ["zeek", "-C", "-i", "ens33", "local", "/usr/local/zeek/share/zeek/site/wazuh_log.zeek"]
