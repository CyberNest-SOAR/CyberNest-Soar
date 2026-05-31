@'
# Velociraptor (EDR) - Sensor Template

## Run
docker compose up -d

## Web UI
http://localhost:8000

## Ports
- 8000: Web UI
- 8889: Agents

## Config
Copy .env.example to .env locally (do NOT commit .env)

## Notes
Velociraptor runs as a standalone EDR server. Collected results are consumed via API, not filesystem JSON files.
'@ | Set-Content sensors\edr\velociraptor\README.md -Encoding UTF8
