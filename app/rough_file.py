from app.config import GRAFANA_API_URL, HEADERS
from app.logger import log_action
import requests

def add_external_group_to_team(team_id: int, group_id: str):
    """
    Associate an external auth provider group with a Grafana team to enable sync.
    """
    url = f"{GRAFANA_API_URL}/api/teams/{team_id}/groups"
    payload = {"groupId": group_id}
    try:
        resp = requests.post(url, headers=HEADERS, json=payload, verify=False)
        if resp.status_code == 400 and "already added" in resp.text:
            log_action("warn", f"External group {group_id} already linked to team {team_id}", "external_sync", group_id)
            return
        resp.raise_for_status()
        log_action("info", f"Added external group {group_id} to team {team_id}", "external_sync", group_id)
    except Exception as e:
        log_action("error", f"Failed to add external group {group_id} to team {team_id}: {e}", "external_sync", group_id)
        raise
