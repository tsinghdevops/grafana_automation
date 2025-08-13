import requests
from app.config import GRAFANA_API_URL, GRAFANA_API_KEY
from app.logger import log_action


HEADERS = {
    "Authorization": f"Bearer {GRAFANA_API_KEY}",
    "Content-Type": "application/json"
}

def get_team_by_name(name: str):
    url = f"{GRAFANA_API_URL}/api/teams/search?name={name}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    if data.get("totalCount", 0) > 0:
        return data["teams"][0]["id"]
    return None

def create_or_get_team(team_name: str) -> int:
    existing_id = get_team_by_name(team_name)
    if existing_id:
        # Log WARNING
        log_action(
            "warn",
            f"Team already exists with ID {existing_id}",
            "team_name",
            team_name
        )
        # Throw Error to client
        raise HTTPException(
            status_code=400,
            detail=f"Team '{team_name}' already exists with ID {existing_id}"
        )
    # If not exists, create
    resp = requests.post(f"{GRAFANA_API_URL}/api/teams", json={"name": team_name}, headers=HEADERS)
    resp.raise_for_status()
    team_id = resp.json()["teamId"]
    log_action(
        "info",
        f"Team created successfully with ID {team_id}",
        "team_name",
        team_name
    )
    return team_id


def get_folder_by_title(title: str):
    url = f"{GRAFANA_API_URL}/api/search?type=dash-folder&query={title}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    results = resp.json()
    for f in results:
        if f.get("title") == title:
            return f.get("uid")
    return None

from fastapi import HTTPException
from app.logger import log_action

def create_or_get_folder(folder_title: str) -> str:
    existing_uid = get_folder_by_title(folder_title)
    if existing_uid:
        # Log WARNING
        log_action(
            "warn",
            f"Folder already exists with UID {existing_uid}",
            "folder_name",
            folder_title
        )
        # Throw Error to client
        raise HTTPException(
            status_code=400,
            detail=f"Folder '{folder_title}' already exists with UID {existing_uid}"
        )
    # If not exists, create
    resp = requests.post(f"{GRAFANA_API_URL}/api/folders", json={"title": folder_title}, headers=HEADERS)
    resp.raise_for_status()
    uid = resp.json()["uid"]
    log_action(
        "info",
        f"Folder created successfully with UID {uid}",
        "folder_name",
        folder_title
    )
    return uid


def merge_folder_permissions(folder_uid: str, team_perms: dict):
    # team_perms: dict(team_id -> permission_code)
    url = f"{GRAFANA_API_URL}/api/folders/{folder_uid}/permissions"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    existing = resp.json()

    # Remove old items for our teams (by teamId), keep others untouched
    existing = [item for item in existing if not (item.get("teamId") in team_perms)]

    # Add/replace our team permissions
    for tid, perm in team_perms.items():
        existing.append({
            "teamId": tid,
            "permission": perm
        })

    # POST merged permissions
    post_payload = {"items": existing}
    post_resp = requests.post(url, json=post_payload, headers=HEADERS)
    post_resp.raise_for_status()

    log_action(
        "info",  # log-level
        f"Permissions merged successfully: {team_perms}",  # message
        "folder_name",  # resource_type
        folder_uid  # resource_value
    )
