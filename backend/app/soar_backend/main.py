from fastapi import FastAPI, Depends
from routers import alerts, risk, patch, filtering, playbooks, intel

app = FastAPI(
    title="SOAR Unified API",
    description="Backend API for Wazuh/OpenSearch SOAR System",
    version="1.0.0"
)

# Include all team routers
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(patch.router, prefix="/api/v1")
app.include_router(filtering.router, prefix="/api/v1")
app.include_router(playbooks.router, prefix="/api/v1")
app.include_router(intel.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "SOAR API is online", "version": "v1"}
