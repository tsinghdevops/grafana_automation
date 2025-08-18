import requests
import json
import datetime
import yaml

# Disable warnings related to insecure requests
requests.packages.urllib3.disable_warnings()

# Load configuration from 'config.json'
with open('config.json') as f:
    config = json.load(f)

logs = []

def log(level, message, resource_name):
    log_entry = {
        "log-level": level,
        "resource_name": resource_name,
        "message": message,
        "executed": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    print(json.dumps(log_entry))
    logs.append(log_entry)

def save_logs(filename="output_generated.json"):
    with open(filename, 'w') as f:
        json.dump(logs, f, indent=4)

# Assign variables from config
grafana_base_url = config.get('grafana_url')
grafana_api_token = config.get('api_token')
group_name = config.get('group_name')

if not grafana_base_url or not grafana_api_token:
    raise Exception("Grafana URL or API token is missing in the configuration!")

headers = {
    "Authorization": f"Bearer {grafana_api_token}",
    "Content-type": "application/json",
    "Accept": "application/json"
}

# ############ Helper Functions ############

def check_folder_exists(folder_name):
    resource_name = f"folder_name:{folder_name}"
    url = f"{grafana_base_url}/api/folders"
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        msg = f"Failed to list folders. Status code: {response.status_code}"
        log("error", msg, resource_name)
        log("error", f"Response: {response.text}", resource_name)
        raise Exception("Cannot proceed without listing folders.")
    folders = response.json()
    for folder in folders:
        if folder.get('title') == folder_name:
            log("info", f"Folder {folder_name} already exists with UID: {folder.get('uid')}", resource_name)
            return True, folder.get('uid')
    log("info", f"Folder {folder_name} does not exist.", resource_name)
    return False, None

def create_folder(folder_name):
    payload = {"title": folder_name}
    response = requests.post(f"{grafana_base_url}/api/folders", json=payload, headers=headers, verify=False)
    resource_name = f"create_folder:{folder_name}"
    if response.status_code == 200:
        folder = response.json()
        log("info", f"Success, Folder '{folder_name}' created with UID: {folder.get('uid')}", resource_name)
        return folder.get('uid')
    elif response.status_code == 409:
        log("warn", f"{response.status_code}: Folder '{folder_name}' already exists. Fetching existing folder.", resource_name)
        exists, uid = check_folder_exists(folder_name)
        if exists:
            return uid
        else:
            log("error", f"Folder exists but failed to fetch UID.", resource_name)
            raise Exception(f"Folder exists but failed to fetch UID.")
    else:
        log("error", f"{response.status_code}, Failed to create folder. {response.text}", resource_name)
        raise Exception("Failed to create folder")

def create_team(team_name):
    resource_name = "teams_api"
    url = f"{grafana_base_url}/api/teams"
    payload = {"name": team_name}
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 200:
        team_id = response.json().get('teamId')
        log("info", f"Success, Team '{team_name}' created with ID: {team_id}", f"create_{resource_name}")
        return team_id
    elif response.status_code == 409:
        # Already exists, fetch id
        search_response = requests.get(f"{grafana_base_url}/api/teams/search?name={team_name}", headers=headers, verify=False)
        if search_response.status_code == 200:
            teams = search_response.json().get("teams", [])
            for team in teams:
                if team.get("name") == team_name:
                    log("info", f"Found existing team '{team_name}' with ID: {team.get('id')}", f"search_{resource_name}")
                    return team.get("id")
            log("error", f"Team '{team_name}' not found in search results.", "search_api_response")
        else:
            log("error", f"Failed to search for team. {search_response.text}", "search_api_response")
        raise Exception("Failed to search for team")
    else:
        log("error", f"Failed to create team '{team_name}'. Status: {response.status_code} {response.text}", f"create_{resource_name}")
        raise Exception("Failed to create team")

def set_folder_permissions(folder_uid, team_permissions):
    resource_name = "set_folder_permissions_api"
    url = f"{grafana_base_url}/api/folders/{folder_uid}/permissions"
    payload = {"items": team_permissions}
    response = requests.post(url, json=payload, headers=headers, verify=False)
    if response.status_code == 200:
        log("info", f"{response.status_code}: Success, Folder permissions set.", resource_name)
        return True
    else:
        log("error", f"{response.status_code}: Failed to set permissions. {response.text}", resource_name)
        return False

def create_datasource(name, team_id):
    # Checks if a datasource with the name already exists
    url = f"{grafana_base_url}/api/datasources"
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        datasources = response.json()
        for ds in datasources:
            if ds.get("name") == name:
                return True, ds.get('id')  # Exists
        return False, None
    else:
        print(f"Failed to fetch datasources. Status code: {response.status_code}")
        return False, None

def datasource_permission(team_id, ds_id, permission):
    # Assign permission for datasource to team
    endpoint = f"{grafana_base_url}/api/datasources/{ds_id}/permissions"
    # Convert string to numeric if needed
    if isinstance(permission, str):
        if permission.lower() == "query":
            perm_val = 1
        elif permission.lower() == "admin":
            perm_val = 2
        else:
            perm_val = 1
    else:
        perm_val = permission
    payload = {
        "teamId": team_id,
        "permission": perm_val
    }
    response = requests.post(endpoint, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        print(f"Permission {perm_val} granted to team {team_id} for datasource {ds_id}.")
        log("info", f"Datasource permission {perm_val} granted to team {team_id} for datasource {ds_id}.", "datasource_permission")
    else:
        print(f"Error: {response.status_code}\nDetails: {response.text}")
        log("error", f"Failed to set datasource permission for team {team_id} and ds {ds_id}.", "datasource_permission")

################# MAIN WORKFLOW #####################

def main():
    folder_name = f"{group_name}-folder"
    team_names = {
        "admin": f"{group_name}-admin",
        "editor": f"{group_name}-editor",
        "readonly": f"{group_name}-readonly"
    }

    # ------- Step 1. Create Teams -------
    team_ids = {}
    print("\nCreating teams...")
    for role, name in team_names.items():
        try:
            team_id = create_team(name)
            team_ids[role] = team_id
        except Exception as e:
            log("error", str(e), f"team_create:{name}")
            save_logs()
            return

    # ------- Step 2. Create datasource from YAML -------
    with open('datasource.yml', 'r') as file:
        yaml_data = yaml.safe_load(file)
    datasource = yaml_data['datasources'][0]
    datasource_json = {
        "name": datasource.get("name"),
        "type": datasource.get("type"),
        "access": datasource.get("access", "proxy"),
        "url": datasource.get("url"),
        "isDefault": datasource.get("isDefault", False),
        "jsonData": datasource.get("jsonData", {})
    }

    # ------- Step 3. Check for existing datasource before creating -------
    already_exists, ds_id = create_datasource(datasource_json['name'], team_ids.get('admin'))
    if already_exists:
        print(f"Warning: Datasource {datasource_json['name']} already exists. Skipping creation.")
    else:
        response = requests.post(f"{grafana_base_url}/api/datasources", headers=headers, data=json.dumps(datasource_json), verify=False)
        if response.status_code in [200, 201]:
            print(f"Datasource created successfully: {response.json()}")
            ds_id = response.json().get('id')
        else:
            print(f"Failed to create datasource. Status code: {response.status_code}, Response: {response.text}")
            ds_id = None

    # ------- Step 4. Create folder (if not exists) -------
    print("\nChecking if folder already exists...")
    try:
        folder_exists, folder_uid = check_folder_exists(folder_name)
        if folder_exists:
            print(f"Folder already exists. Exiting.")
            save_logs()
        else:
            print("\nCreating new folder...")
            folder_uid = create_folder(folder_name)
    except Exception as e:
        log("error", str(e), f"folder_name:{folder_name}")
        save_logs()
        return

    # ------- Step 5. Set folder permissions -------
    print("\nSetting folder permissions...")
    team_permissions = [
        {"teamId": team_ids["admin"], "permission": 4},    # Admin
        {"teamId": team_ids["editor"], "permission": 2},   # Editor
        {"teamId": team_ids["readonly"], "permission": 1}  # Read
    ]
    try:
        success = set_folder_permissions(folder_uid, team_permissions)
        if success:
            log("info", "All folder permissions set successfully.", f"folder_name:{folder_name}")
        else:
            log("error", "Failed to set folder permissions.", f"folder_name:{folder_name}")
        save_logs()
    except Exception as e:
        log("error", str(e), f"folder_name:{folder_name}")
        save_logs()
        return

    # ------- Step 6. Set datasource permissions for teams -------
    if ds_id:
        # Map your desired role to datasource permission (admin:2, editor:1, readonly:1)
        role_perms = {"admin": 2, "editor": 1, "readonly": 1}
        for role, team_id in team_ids.items():
            datasource_permission(team_id, ds_id, role_perms[role])
    else:
        print("Datasource ID not found, skipping datasource permission assignment.")

    # ------- END -------
    save_logs()
    print("All operations completed.")

if __name__ == "__main__":
    main()
