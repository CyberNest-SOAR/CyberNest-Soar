@'
# Arkime (NDR) Sensor

## Description
Arkime Network Detection & Response sensor.
Parses PCAP files and stores sessions in OpenSearch.

## Run
docker compose up -d

## Init DB (first time)
docker compose run --rm arkime-viewer /opt/arkime/db/db.pl http://opensearch:9200 init

## Web UI
http://localhost:8005

## Create Admin User (demo)
docker compose exec arkime-viewer /opt/arkime/bin/arkime_add_user.sh admin "Admin User" admin --admin

## PCAP Ingest (manual)
docker compose run --rm arkime-capture bash -lc "cd /opt/arkime && /opt/arkime/bin/capture -r /data/pcap/<file>.pcap"

## Verify
GET http://localhost:9200/arkime_sessions*/_search
'@ | Set-Content README.md -Encoding UTF8
