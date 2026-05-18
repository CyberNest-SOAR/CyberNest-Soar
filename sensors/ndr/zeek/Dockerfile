FROM zeek/zeek:latest

USER root

RUN apt-get update && apt-get install -y iproute2 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/zeek/logs

WORKDIR /opt/zeek

COPY zeek/policy /opt/zeek/share/zeek/policy
COPY zeek /opt/zeek/share/zeek/site
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
