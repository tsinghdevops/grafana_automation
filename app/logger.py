import logging
import json
from pythonjsonlogger import jsonlogger

LOG_FILE = "grafana_automation.log.json"

logger = logging.getLogger("grafana_logger")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE)
# We don't use jsonlogger default fields; we control JSON formatting ourselves
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
logger.handlers = [file_handler]


def log_action(level: str, message: str, resource_type: str, resource_value: str):
    """
    level: "info", "warn", "error"
    message: actual log message
    resource_type: "folder_name" or "team_name"
    resource_value: the folder or team name
    """
    log_entry = {
        "log-level": level,
        "message": message,
        "resource_name": f"{resource_type}: {resource_value}"
    }
    logger.info(json.dumps(log_entry))
