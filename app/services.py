from app.logger import log_action
from app.models import ADGroupRoles
from app.grafana_client import create_or_get_folder, create_or_get_team, merge_folder_permissions


def process_ad_group_roles(payload: ADGroupRoles):
    log_action("info", "Processing request started", "folder_name", payload.accountName)

    folder_uid = create_or_get_folder(payload.accountName)
    readonly_team_id = create_or_get_team(payload.readonly)
    readwrite_team_id = create_or_get_team(payload.readwrite)
    admin_team_id = create_or_get_team(payload.admin)

    team_perms = {
        readonly_team_id: 1,
        readwrite_team_id: 2,
        admin_team_id: 4
    }
    merge_folder_permissions(folder_uid, team_perms)

    log_action("info", "Processing request completed", "folder_name", payload.accountName)

    return {
        "status": "success",
        "folder_uid": folder_uid,
        "teams": {
            "readonly": readonly_team_id,
            "readwrite": readwrite_team_id,
            "admin": admin_team_id
        }
    }
