# suricata-lab/Dockerfile
FROM jasonish/suricata:latest

USER root

# Create directories
RUN mkdir -p /etc/suricata/rules
RUN mkdir -p /var/log/suricata

# Copy config and rules
COPY suricata/suricata.yaml /etc/suricata/suricata.yaml
COPY suricata/rules/ /etc/suricata/rules/

CMD ["-c", "/etc/suricata/suricata.yaml", "-i", "ens33"]
