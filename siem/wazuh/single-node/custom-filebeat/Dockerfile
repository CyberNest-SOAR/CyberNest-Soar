FROM wazuh/wazuh-manager:4.14.4 AS wazuh

FROM alpine:3.19
RUN apk add --no-cache ca-certificates bash gcompat && \
    ln -sf /lib/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2
COPY --from=wazuh /usr/bin/filebeat /usr/bin/filebeat
COPY --from=wazuh /usr/share/filebeat/bin /usr/share/filebeat/bin
RUN mkdir -p /usr/share/filebeat /etc/filebeat /var/lib/filebeat /var/log/filebeat
WORKDIR /usr/share/filebeat
ENTRYPOINT ["/usr/bin/filebeat"]
CMD ["-e", "--strict.perms=false", "-c", "/etc/filebeat/filebeat.yml"]
