from fastapi import FastAPI, HTTPException
from app.models import ADGroupRoles
from app.services import process_ad_group_roles

app = FastAPI(title="Grafana Automation Microservice")

@app.post("/create-grafana-resources")
async def create_grafana_resources(payload: ADGroupRoles):
    try:
        result = process_ad_group_roles(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
