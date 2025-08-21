def get_datasource_by_name(ds_name: str):
    url = f"{GRAFANA_API_URL}/api/datasources"
    resp = requests.get(url, headers=HEADERS, verify=False)
    resp.raise_for_status()
    for ds in resp.json():
        if ds.get("name") == ds_name:
            return ds["uid"]  # or ds["id"] if preferred, but UID is used for permissions!
    return None

def create_or_get_datasource(ds_payload: dict) -> str:
    existing_uid = get_datasource_by_name(ds_payload["name"])
    if existing_uid:
        log_action("warn", f"Datasource already exists with UID {existing_uid}", "datasource_name", ds_payload["name"])
        return existing_uid
    # If not found, create new
    url = f"{GRAFANA_API_URL}/api/datasources"
    resp = requests.post(url, headers=HEADERS, json=ds_payload, verify=False)
    resp.raise_for_status()
    ds_uid = resp.json()["uid"]
    log_action("info", f"Datasource created with uid {ds_uid}", "datasource_name", ds_payload["name"])
    return ds_uid
