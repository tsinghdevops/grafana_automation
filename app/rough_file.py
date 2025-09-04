from fastapi import FastAPI, HTTPException, Request
import yaml

app = FastAPI()

@app.post("/create_datasource")
async def create_datasource(request: Request):
    try:
        # Read raw body bytes
        raw_body = await request.body()
        # Parse YAML to Python dict
        payload = yaml.safe_load(raw_body)
    except yaml.YAMLError:
        raise HTTPException(status_code=422, detail="Invalid YAML payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        # Pass the parsed dict payload to your existing service function
        return create_or_get_datasource(payload)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
